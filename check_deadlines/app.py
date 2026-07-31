import os
import json
from datetime import datetime, timedelta
import boto3

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

table_name = os.environ.get('TABLE_NAME', 'ReturnGuardItems')
alert_email = os.environ.get('ALERT_EMAIL')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    if not alert_email:
        print("ALERT_EMAIL environment variable not set. Aborting.")
        return
        
    today = datetime.utcnow().date()
    warning_threshold = today + timedelta(days=3)
    
    response = table.scan()
    items = response.get('Items', [])
    
    urgent_items = []
    for item in items:
        if item.get('status') != 'ACTIVE':
            continue
        try:
            return_date = datetime.strptime(item['returnByDate'], '%Y-%m-%d').date()
            if today <= return_date <= warning_threshold:
                urgent_items.append(item)
        except ValueError:
            continue
            
    if not urgent_items:
        print("No items expiring within 3 days.")
        return {"status": "No alerts needed"}
        
    email_body = "ReturnGuard Action Required: The following return windows are closing soon!\n\n"
    for item in urgent_items:
        email_body += f"- {item['itemName']} ({item['retailer']}) - Price: {item['price']}\n"
        email_body += f"  Deadline: {item['returnByDate']}\n"
        email_body += f"  Drafted Return Message: 'Hello {item['retailer']} Support, I would like to initiate a return for {item['itemName']} purchased on {item['purchaseDate']}. Please send return instructions.'\n\n"
        
    try:
        ses.send_email(
            Source=alert_email,
            Destination={'ToAddresses': [alert_email]},
            Message={
                'Subject': {'Data': f"⚠️ ReturnGuard Alert: {len(urgent_items)} return window(s) closing soon!"},
                'Body': {'Text': {'Data': email_body}}
            }
        )
        print(f"Sent email alert for {len(urgent_items)} item(s).")
    except Exception as e:
        print(f"Failed to send SES email: {str(e)}")
        
    return {"status": "Checked", "alertsSent": len(urgent_items)}
