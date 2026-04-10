"""
Lambda function: ECS Rollback on CloudWatch Alarm
--------------------------------------------------
Triggered by SNS when a CloudWatch alarm fires (ALB 5xx or ECS unhealthy tasks).
It finds the previous stable ECS task definition revision and updates the ECS
service to roll back to it automatically.
Sends an email notification via SNS after rollback is initiated.
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


def get_previous_task_definition(family):
    """Return the ARN of the second-latest (previous stable) task definition."""
    response = ecs.list_task_definitions(
        familyPrefix=family,
        sort='DESC',
        status='ACTIVE'
    )
    arns = response.get('taskDefinitionArns', [])
    if len(arns) < 2:
        logger.warning('No previous task definition found to roll back to.')
        return None
    return arns[1]  # [0] = current (broken), [1] = previous stable


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

    # Get current task definition family from the running service
    svc = ecs.describe_services(cluster=CLUSTER, services=[SERVICE])
    service_detail = svc['services'][0]
    current_task_def_arn = service_detail['taskDefinition']
    family = current_task_def_arn.split('/')[1].split(':')[0]

    logger.info('Current task definition: %s', current_task_def_arn)
    logger.info('Task definition family: %s', family)

    previous_task_def_arn = get_previous_task_definition(family)
    if not previous_task_def_arn:
        msg = (
            f'ECS Rollback ABORTED for service {SERVICE} in cluster {CLUSTER}.\n'
            f'Reason: No previous task definition found.\n'
            f'Current task definition: {current_task_def_arn}\n'
            f'Manual intervention required!'
        )
        send_notification('[ACTION REQUIRED] ECS Rollback Aborted - No Previous Version', msg)
        logger.error('Rollback aborted: no previous task definition available.')
        return {'status': 'ABORTED', 'reason': 'No previous task definition found'}

    logger.info('Rolling back to: %s', previous_task_def_arn)

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
        f'Failed version  : {current_task_def_arn}\n'
        f'Rolled back to  : {previous_task_def_arn}\n\n'
        f'Reason: CloudWatch alarm detected unhealthy deployment.\n'
        f'Please investigate the failed deployment and fix the issue before redeploying.'
    )
    send_notification('[ALERT] ECS Automatic Rollback Initiated', msg)

    logger.info('Rollback initiated successfully.')
    return {
        'status': 'ROLLBACK_INITIATED',
        'rolledBackTo': previous_task_def_arn
    }
