import mechanicalsoup

def verify_data(user_id, password):
    browser = mechanicalsoup.StatefulBrowser()
    url = "http://14.139.108.229/W27/login.aspx"
    browser.open(url)
    browser.get_current_page()
    browser.select_form()
    browser["txtUserName"] = user_id
    browser["Password1"] = password
    browser.submit_selected()
    span_id = "ctl00_lblUsername"  
    page = browser.page
    messages =page.find_all('span', attrs={"id" : span_id})
    if messages:
        return True
    else:
        return False