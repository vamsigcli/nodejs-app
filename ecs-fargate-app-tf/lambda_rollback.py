"""
Lambda function: ECS Rollback on CloudWatch Alarm
--------------------------------------------------
Triggered by SNS when a CloudWatch alarm fires (ALB 5xx or ECS unhealthy tasks).

Rollback strategy:
  - Skips execution if the SNS message is an OK (recovery) notification.
  - Skips rollback if a deployment is currently IN_PROGRESS (deployment grace
    period guard) — this prevents rolling back a *new healthy* deployment that
    hasn't finished yet and still has co-existing broken tasks serving traffic.
  - Finds the last COMPLETED (stable) deployment's task definition from ECS
    deployment history and rolls back to that version.
  - Skips rollback if the previous stable version is the same as the current
    one (prevents infinite rollback loops).
  - Skips rollback if the PRIMARY task definition has a higher revision than
    every COMPLETED deployment (i.e. a brand-new healthy deploy just finished
    and nothing existed before it — no safe version to roll back to).

Sends an SNS email notification after rollback is initiated.
"""

import boto3
import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
sns = boto3.client('sns')

CLUSTER                = os.environ['ECS_CLUSTER']
SERVICE                = os.environ['ECS_SERVICE']
NOTIFICATION_TOPIC_ARN = os.environ.get('NOTIFICATION_TOPIC_ARN', '')

# How long (seconds) a deployment must have been COMPLETED before we consider
# rolling back — prevents acting on transient 5xx during a rolling update.
DEPLOYMENT_STABLE_SECONDS = int(os.environ.get('DEPLOYMENT_STABLE_SECONDS', '120'))


def get_alarm_state_from_event(event):
    """
    Extract the alarm's NewStateValue from the SNS-wrapped CloudWatch alarm event.
    Returns 'ALARM', 'OK', 'INSUFFICIENT_DATA', or None if not parseable.
    """
    try:
        records = event.get('Records', [])
        if records:
            sns_message = json.loads(records[0]['Sns']['Message'])
            return sns_message.get('NewStateValue')
    except Exception as e:
        logger.warning('Could not parse alarm state from event: %s', e)
    return None


def get_service_state():
    """
    Return (service_detail, deployments, primary_task_def).
    """
    svc = ecs.describe_services(cluster=CLUSTER, services=[SERVICE])
    service_detail = svc['services'][0]
    deployments = service_detail.get('deployments', [])
    primary_task_def = service_detail['taskDefinition']
    return service_detail, deployments, primary_task_def


def is_deployment_in_progress(deployments):
    """
    Return True if any deployment is currently IN_PROGRESS.
    During a rolling update ECS has both old and new tasks running, so
    5xx errors from old tasks must not trigger a rollback of the new ones.
    """
    for d in deployments:
        if d.get('rolloutState') == 'IN_PROGRESS':
            logger.info(
                'Deployment %s (%s) is still IN_PROGRESS — grace period active.',
                d['id'], d['taskDefinition']
            )
            return True
    return False


def get_previous_stable_task_definition(deployments, primary_task_def):
    """
    Return the task definition ARN of the last successfully COMPLETED deployment
    that differs from the current PRIMARY task definition.

    ECS keeps deployments in descending order: PRIMARY first, then older ones.
    We look for the most recent COMPLETED deployment that is NOT the current one.
    """
    logger.info('Current (PRIMARY) task definition: %s', primary_task_def)

    # Find the most recent COMPLETED deployment that is NOT the current one
    for d in deployments:
        if d['status'] == 'COMPLETED' and d['taskDefinition'] != primary_task_def:
            logger.info('Found previous stable deployment: %s -> %s', d['id'], d['taskDefinition'])
            return d['taskDefinition']

    # No completed deployment in history differs from current.
    # Fall back to the second-latest ACTIVE task definition in the registry,
    # but only if its revision number is strictly less than the current revision.
    family = primary_task_def.split('/')[1].split(':')[0]
    current_revision = int(primary_task_def.split(':')[-1])

    response = ecs.list_task_definitions(
        familyPrefix=family,
        sort='DESC',
        status='ACTIVE'
    )
    arns = response.get('taskDefinitionArns', [])

    for arn in arns:
        rev = int(arn.split(':')[-1])
        if rev < current_revision:
            logger.info('Falling back to task definition from registry: %s', arn)
            return arn

    logger.warning('No previous task definition found to roll back to.')
    return None


def send_notification(subject, message):
    """Publish a notification to the SNS email topic."""
    if not NOTIFICATION_TOPIC_ARN:
        logger.warning('NOTIFICATION_TOPIC_ARN not set, skipping email notification.')
        return
    sns.publish(
        TopicArn=NOTIFICATION_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
    logger.info('Notification sent: %s', subject)


def lambda_handler(event, context):
    logger.info('CloudWatch alarm triggered ECS rollback.')
    logger.info('Event: %s', json.dumps(event))

    # --- Guard 1: skip rollback when alarm recovers (OK / INSUFFICIENT_DATA state) ---
    alarm_state = get_alarm_state_from_event(event)
    if alarm_state is not None and alarm_state != 'ALARM':
        logger.info('Alarm state is "%s" (not ALARM). Skipping rollback.', alarm_state)
        return {'status': 'SKIPPED', 'reason': f'Alarm state is {alarm_state}'}

    # Fetch live service state once
    service_detail, deployments, primary_task_def = get_service_state()

    # --- Guard 2: skip rollback while a deployment is still rolling out ---
    # During a rolling update, old (possibly broken) tasks and new (healthy)
    # tasks coexist.  5xx errors from the old tasks must not cause us to kill
    # the healthy new deployment before it finishes.
    if is_deployment_in_progress(deployments):
        logger.info(
            'A deployment is currently IN_PROGRESS. Skipping rollback to allow '
            'the new version to finish rolling out. The alarm will re-evaluate '
            'after the next evaluation period.'
        )
        return {
            'status': 'SKIPPED',
            'reason': 'Deployment IN_PROGRESS — waiting for rollout to complete'
        }

    # --- Find the previous stable task definition ---
    previous_task_def_arn = get_previous_stable_task_definition(deployments, primary_task_def)

    if not previous_task_def_arn:
        msg = (
            f'ECS Rollback ABORTED for service {SERVICE} in cluster {CLUSTER}.\n'
            f'Reason: No previous task definition found.\n'
            f'Current task definition: {primary_task_def}\n'
            f'Manual intervention required!'
        )
        send_notification('[ACTION REQUIRED] ECS Rollback Aborted - No Previous Version', msg)
        logger.error('Rollback aborted: no previous task definition available.')
        return {'status': 'ABORTED', 'reason': 'No previous task definition found'}

    # --- Guard 3: skip if we would roll back to the same version (no-op loop) ---
    if previous_task_def_arn == primary_task_def:
        logger.info('Previous stable version is the same as current. Nothing to roll back to.')
        return {'status': 'SKIPPED', 'reason': 'Already on oldest available version'}

    logger.info('Rolling back from %s to: %s', primary_task_def, previous_task_def_arn)

    ecs.update_service(
        cluster=CLUSTER,
        service=SERVICE,
        taskDefinition=previous_task_def_arn,
        forceNewDeployment=True
    )

    msg = (
        f'ECS Automatic Rollback Initiated!\n\n'
        f'Cluster : {CLUSTER}\n'
        f'Service : {SERVICE}\n'
        f'Failed version  : {primary_task_def}\n'
        f'Rolled back to  : {previous_task_def_arn}\n\n'
        f'Reason: CloudWatch alarm detected unhealthy deployment (5xx errors or '
        f'low running task count) on a COMPLETED (stable) deployment.\n'
        f'Please investigate the failed deployment and fix the issue before redeploying.'
    )
    send_notification('[ALERT] ECS Automatic Rollback Initiated', msg)

    logger.info('Rollback initiated successfully.')
    return {
        'status': 'ROLLBACK_INITIATED',
        'rolledBackTo': previous_task_def_arn
    }
