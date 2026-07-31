import json
import os
import uuid
import re
from datetime import datetime, timedelta
import boto3

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')
table_name = os.environ.get('TABLE_NAME', 'ReturnGuardItems')
table = dynamodb.Table(table_name)

DEFAULT_RETURN_DAYS = {
    'amazon': 30,
    'target': 90,
    'walmart': 90,
    'best buy': 15,
    'apple': 14,
    'default': 30
}

def fallback_extract(text):
    """Fallback rules-based extraction if Bedrock is unavailable on a new free account."""
    text_lower = text.lower()
    retailer = "Unknown Retailer"
    for r in DEFAULT_RETURN_DAYS.keys():
        if r in text_lower and r != 'default':
            retailer = r.title()
            break
            
    price_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', text)
    price = f"${price_match.group(1)}" if price_match else "$0.00"
    
    item_name = "Imported Online Purchase"
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 3]
    if lines:
        item_name = lines[0][:50]
        
    purchase_date = datetime.utcnow().strftime('%Y-%m-%d')
    days = DEFAULT_RETURN_DAYS.get(retailer.lower(), DEFAULT_RETURN_DAYS['default'])
    return_by = (datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    return {
        "retailer": retailer,
        "itemName": item_name,
        "price": price,
        "purchaseDate": purchase_date,
        "returnByDate": return_by,
        "extractionMethod": "Fallback-Rules"
    }

def extract_with_bedrock(text):
    """Extract structured purchase data using Amazon Bedrock (Nova Lite)."""
    prompt = f"""
    Extract purchase details from the text below and return ONLY valid JSON with exactly these keys:
    "retailer" (string), "itemName" (string), "price" (string with $), "purchaseDate" (YYYY-MM-DD), "returnByDate" (YYYY-MM-DD).
    If returnByDate is not explicitly stated, estimate it based on standard retailer policy (default 30 days from purchase).
    
    Text:
    {text}
    """
    
    payload = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"max_new_tokens": 300, "temperature": 0.1}
    }
    
    try:
        response = bedrock.invoke_model(
            modelId="amazon.nova-lite-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        response_body = json.loads(response['body'].read())
        content_text = response_body['output']['message']['content'][0]['text']
        
        clean_json = re.sub(r'```json\s*|\s*```', '', content_text).strip()
        data = json.loads(clean_json)
        data['extractionMethod'] = "Amazon-Bedrock"
        return data
    except Exception as e:
        print(f"Bedrock invocation failed ({str(e)}). Switching to fallback rules engine.")
        return fallback_extract(text)

def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    
    if method == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
            }
        }
        
    if method == 'GET':
        try:
            response = table.scan()
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('returnByDate', '9999-99-99'))
            return {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(items)
            }
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    if method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            raw_text = body.get('text', '')
            if not raw_text:
                return {"statusCode": 400, "body": json.dumps({"error": "No text provided"})}
                
            extracted = extract_with_bedrock(raw_text)
            
            item_id = str(uuid.uuid4())
            item_record = {
                "itemId": item_id,
                "retailer": extracted.get('retailer', 'Unknown'),
                "itemName": extracted.get('itemName', 'Item'),
                "price": extracted.get('price', '$0.00'),
                "purchaseDate": extracted.get('purchaseDate', datetime.utcnow().strftime('%Y-%m-%d')),
                "returnByDate": extracted.get('returnByDate', (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d')),
                "status": "ACTIVE",
                "extractionMethod": extracted.get('extractionMethod', 'Unknown'),
                "createdAt": datetime.utcnow().isoformat()
            }
            
            table.put_item(Item=item_record)
            
            return {
                "statusCode": 201,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(item_record)
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": str(e)})
            }
