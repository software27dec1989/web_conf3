from flask import Flask, render_template, request, jsonify
import requests
import time
import re

app = Flask(__name__)

confluence_url = "https://abc-confluence.systems.uk.asdc/confluence"
parent_page_id = "065625"
api_url = f"{confluence_url}/rest/api/content/{parent_page_id}/child/page"

def get_all_child_pages(api_url, bearer_token):
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    child_pages = []
    retry_attempts = 5
    while api_url:
        for attempt in range(retry_attempts):
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                child_pages.extend(response_data.get("results", []))
                
                next_page_url = response_data.get("_links", {}).get("next")
                if next_page_url:
                    api_url = confluence_url + next_page_url
                else:
                    api_url = None
                break
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                time.sleep(retry_after)
            else:
                break
    return child_pages

def extract_change_number(title):
    match = re.search(r'(CHG|CR)\d+', title)
    if match:
        return match.group(0)
    return None

def search_page_by_change_number(child_pages, change_number):
    for page in child_pages:
        title = page.get("title")
        webui = page.get("_links", {}).get("webui")
        
        if webui:
            full_link = confluence_url + webui
            extracted_change_number = extract_change_number(title)
            
            if extracted_change_number == change_number:
                return full_link
    return None

def patch_api(cr_number, update_data, ice_basic_token):
    url = f'https://cie.it.glocal.xyzc/cie/api/v2/changes/{cr_number}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Basic {ice_basic_token}",
    }
    
    data = {
        "change": {
            "businessApprovalUrl": update_data,
            "independentCodeReviewUrl": update_data,
            "testEvidenceUrl": update_data,
            "artifacts": {
                "artifacts": [
                    {
                        "artifactName": "Artifact1",
                        "regressionTestType": 'Partial',
                        "resgressionTestJustification": 'Required Justification for Partial test',
                        "codeReviewUrl": update_data,
                        "sourceCodeUrl": update_data,
                        "manualRegressionTestUrls": [update_data]
                    }
                ]
            },
            "postDeploymentVerificationEvidenceUrl": update_data,
            "manualRegressionTestUrls": [update_data],
            "requirementUrls": [update_data]
        },
        "fieldsToUpdate": [
            "independentCodeReviewUrl",
            "businessApprovalUrl",
            "testEvidenceUrl",
            "postDeploymentVerificationEvidenceUrl",
            "manualRegressionTestUrls",
            "performanceStressTestEvidenceUrl",
            "artifacts"
        ]
    }
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Failed to update Change Number {cr_number}, status code: {response.status_code}, message: {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_changes():
    bearer_token = request.form.get('bearerToken')
    ice_basic_token = request.form.get('iceToken')
    change_numbers = request.form.get('changeNumbers')
    
    change_numbers = [num.strip() for num in change_numbers.split(",")]
    
    child_pages = get_all_child_pages(api_url, bearer_token)
    
    results = {}
    for change_number in change_numbers:
        confluence_link = search_page_by_change_number(child_pages, change_number)
        
        if confluence_link:
            update_result = patch_api(change_number, confluence_link, ice_basic_token)
            results[change_number] = update_result
        else:
            results[change_number] = f"No page found for {change_number}"
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
