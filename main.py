import requests, pycurl_requests, pycurl, requests_oauthlib, bs4, json, re, pandas, datetime, time, os, sys
import selenium, selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def parse_product(config, product_id, subcategory = ""):
    time.sleep(1)
    try:
        with pycurl_requests.Session() as session:
            session.curl.setopt(pycurl.PROXY, proxy)
            product_response = session.get(f"https://store.playstation.com/ru-ua/product/{product_id}", timeout=30)
            time.sleep(2)
            product_response_trl_price = session.get(f"https://store.playstation.com/en-tr/product/{product_id}", timeout=30)
            if "access denied" in product_response.text.lower() or "access denied" in product_response_trl_price.text.lower():
                set_proxy(config)
            product_soup_trl_price = bs4.BeautifulSoup(product_response_trl_price.text, "html.parser")
            product_json_price = json.loads(product_soup_trl_price.find("div", attrs={"class": "pdp-cta"}).find("script").text)
            product_soup = bs4.BeautifulSoup(product_response.text, "html.parser")
            product_json_env_text = product_soup.find("div", attrs={"class": "pdp-cta"}).find("script").text
            product_json = json.loads(product_soup.find("script", attrs={"id": "__NEXT_DATA__", "type": "application/json"}).text)
            product_json_general_text = product_soup.find("script", attrs={"id": "mfe-jsonld-tags", "type": "application/ld+json"}).text
            product_json_game_title = json.loads(product_soup_trl_price.find("div", attrs={"class": "pdp-game-title"}).find("script").text)
            product_edition = product_json_game_title["cache"][f"Product:{product_id}"]["edition"]["name"]
            product_json_general = json.loads(product_json_general_text)
            product_json_info = json.loads(product_soup.find("div", attrs={"class": "pdp-info"}).find("script").text)
            product_release_date = ".".join(product_json_info["cache"][f"Product:{product_id}"]["releaseDate"].split("T")[0].split("-")[::-1])
            product_json_cta = json.loads(product_json_env_text)
            product_name = product_json_cta["cache"][f"Product:{product_id}"]["name"]
            product_game_cta = product_json_cta["cache"][f"Product:{product_id}"]["webctas"][0]["__ref"]
            product_json_uah_price = product_json_cta["cache"][product_game_cta]["price"]
            product_json_trl_price = product_json_price["cache"][product_game_cta]["price"]
            product_uah_discounted_price = round(int(product_json_uah_price["discountedValue"]) / 100 * uah_multiplier)
            product_trl_discounted_price = round(int(product_json_trl_price["discountedValue"]) / 100 * trl_multiplier)
            product_uah_base_price = round(int(product_json_uah_price["basePriceValue"]) / 100 * uah_multiplier)
            product_trl_base_price = round(int(product_json_trl_price["basePriceValue"]) / 100 * trl_multiplier)
            product_discount_percent = int(product_json_price["cache"][product_game_cta]["price"]["discountText"][1:-1])
            product_image_url = product_json_general["image"]
            end_time = (int(product_json_cta["cache"][product_game_cta]["price"]["endTime"]) - 86400 * 1000) / 1000
            end_times.append(end_time)
            product_discount_end_date = datetime.datetime.fromtimestamp(end_time).strftime("%d.%m.%Y")
            product_publisher = product_json_game_title["cache"][f"Product:{product_id}"]["publisherName"]
            product_description = product_json["props"]["pageProps"]["batarangs"]["info"]["text"]
            product_description_soup = bs4.BeautifulSoup(product_description, "html.parser")
            product_description_general_string = str(product_soup.find("p", {"data-qa": "mfe-game-overview#description"}))
            product_description_general = "" # product_description_general_string[product_description_general_string.find(">") + 1:product_description_general_string.rfind("<")]
            product_platforms = product_json_game_title["cache"][f"Product:{product_id}"]["platforms"]
            product_add_description = f"<b>Платформы:</b> {' '.join(product_platforms)}<br>"
        try:
            product_screen_languages = f'<p><b>Локализация:</b> {product_description_soup.find("dd", {"data-qa": "gameInfo#releaseInformation#subtitles-value"}).text}</p>'
            # product_russian_language = product_screen_languages.lower().find("рус") != -1
        except:
            product_screen_languages = ""
            # product_russian_language = False
        try:
            product_voices = f'<p><b>Озвучка:</b> {product_description_soup.find("dd", {"data-qa": "gameInfo#releaseInformation#voice-value"}).text}</p>'
            # product_russian_voice = product_voices.lower().find("рус") != -1
        except:
            product_voices = ""
            # product_russian_voice = False
        # if product_russian_language and product_voices:
        # 	product_add_description += f"<b>Язык</b> - Полностью на русском<br>"
        # elif product_russian_language:
        # 	product_add_description += f"<b>Язык</b> - С русскими субтитрами<br>"
        # elif product_russian_voice:
        # 	product_add_description += f"<b>Язык</b> - С русской озвучкой<br>"
        # else:
        # 	product_add_description += f"<b>Язык</b> - Без русского перевода<br>"
        product_description_general = f"<p>{product_add_description}</p>{product_screen_languages}{product_voices}"
        product_description_general+= f"<p style=\"opacity: 0; font-size: 1px;\">id_{product_id}_idend_{subcategory}<p><br>"
    except requests.exceptions.ProxyError:
        set_proxy(config)
    except Exception as e:
        print(f"\n[{datetime.datetime.now()}] {e}")
        return
    if product_id in result["ID"]:
        return True
    if end_time < int(datetime.datetime.today().timestamp()):
        return
    result["ID"].append(product_id)
    result["Category"].append("Распродажа")
    result["Name"].append(product_name)
    result["Image"].append(product_image_url)
    result["TRL Price Old"].append(product_trl_base_price)
    result["TRL Price"].append(product_trl_discounted_price)
    result["UAH Price Old"].append(product_uah_base_price)
    result["UAH Price"].append(product_uah_discounted_price)
    result["Discount Percent"].append(product_discount_percent)
    result["Publisher"].append(product_publisher)
    result["Discount End Date"].append(product_discount_end_date)
    result["Edition"].append(product_edition)
    result["Release Date"].append(product_release_date)
    result["Description"].append(product_description_general)
    print(f'\rPage: {page_num}    Complite: {len(result["Name"])}   ', end="")
    time.sleep(1)
    return True

def edit_popular_product(oauth: requests_oauthlib.OAuth1, site_url, category_id, product_id, tgshop):
    edit_product_url = f"https://{site_url}/uapi/shop/editgoods"
    data = {
        "method": "submit",
        "cat_id": category_id,
        "id": product_id,
        "type": 1,
        "sort": 1,
        "tg_shop": tgshop
    }
    return requests.post(edit_product_url, data=data, auth=oauth)

def parse_popular(config):
    for site in config["sites"]:
        site_url = site["url"]
        oauth = requests_oauthlib.OAuth1(**site["oauth"])
        popular_category_id = str(site["popular_category_id"])
        if popular_category_id.isdigit():
            popular_category_id = int(popular_category_id)
            current_page_num = 1
            current_products_count = 0
            error_count = 0
            while error_count < 10:
                get_products_response = get_products(oauth, site_url, current_page_num)
                if get_products_response.status_code != 200:
                    error_count += 1
                    continue
                error_count = 0
                try:
                    for _, product_value in get_products_response.json()["success"]["goods_list"].items():
                        current_products_count += 1
                        print(f"\r[{site_url}] Get products: {current_products_count} ", end="")
                        if int(product_value["entry_cat"]["id"]) == popular_category_id:
                            product_description = product_value["entry_description"]
                            current_product_id = product_description[product_description.find("id_") + len("id_"):product_description.find("_idend")]
                            if parse_product(config, current_product_id, "addpopular"):
                                print(edit_popular_product(oauth, site_url, popular_category_id, product_value["entry_id"], 0).content.decode())
                            else:
                                print(edit_popular_product(oauth, site_url, popular_category_id, product_value["entry_id"], 1).content.decode())
                except:
                    break
                current_page_num += 1
            print()

def parser(config, products_count):
    global trl_multiplier, uah_multiplier, end_times, result, page_num, first_end_time
    page_url = "https://store.playstation.com/en-tr/category/83a687fe-bed7-448c-909f-310e74a71b39/"
    filters = "FULL_GAME=storeDisplayClassification&GAME_BUNDLE=storeDisplayClassification&PREMIUM_EDITION=storeDisplayClassification"
    trl_multiplier = float(config["trl_multiplier"])
    uah_multiplier = float(config["uah_multiplier"])
    page_num = 1
    end_times = []
    result = {
        "ID": [],
        "Category": [],
        "Name": [],
        "Image": [],
        "TRL Price Old": [],
        "TRL Price": [],
        "UAH Price Old": [],
        "UAH Price": [],
        "Discount Percent": [],
        "Publisher": [],
        "Discount End Date": [],
        "Edition": [],
        "Release Date": [],
        "Description": []
    }
    parse_popular(config)
    while len(result["Name"]) < products_count:
        try:
            with pycurl_requests.Session() as session:
                session.curl.setopt(pycurl.PROXY, proxy)
                page_response = session.get(f"{page_url}{page_num}?{filters}", timeout=15)
                if "access denied" in page_response.text.lower():
                    set_proxy(config)
                page_num += 1
                if page_response.status_code != 200:
                    continue
                page_soup = bs4.BeautifulSoup(page_response.text, "html.parser")
                page_json_text = page_soup.find("script", attrs={"id": "__NEXT_DATA__", "type": "application/json"}).text
                page_json = json.loads(page_json_text)
                apolloState = page_json["props"]["apolloState"]
                for item in apolloState:
                    if re.fullmatch(r'Product:[A-Za-z-_0-9]+:en-tr', item) and len(result["Name"]) < products_count:
                        try:
                            product_id = item.split(":")[1]
                            parse_product(config, product_id)
                        except:
                            continue
        except requests.exceptions.ProxyError:
            set_proxy(config)
    print()
    data_frame = pandas.DataFrame(result)
    data_frame.to_excel("ps.xlsx", header=False, index=False, engine="xlsxwriter")
    first_end_time = int(min(end_times))
    print(f"[{datetime.datetime.now()}] Parsing complite!")
    time.sleep(10)

def get_products(oauth: requests_oauthlib.OAuth1, site_url, pnum):
    request_url = f"https://{site_url}/uapi/shop/request"
    parameters = {
        "page": "allgoods",
        "pnum": pnum
    }
    return requests.get(request_url, params=parameters, auth=oauth, timeout=60)

def edit_product(oauth: requests_oauthlib.OAuth1, site_url, category_id, product_id, addcategory_id = ""):
    edit_product_url = f"https://{site_url}/uapi/shop/editgoods"
    data = {
        "method": "submit",
        "cat_id": category_id,
        "id": product_id,
        "type": 1,
        "tg_shop": 1
    }
    if addcategory_id != "":
        data["ch_addcat"] = 1
        data["cats_add"] = f"[{addcategory_id}]"
    return requests.post(edit_product_url, data=data, auth=oauth)

def edit_products(config):
    for site in config["sites"]:
        site_url = site["url"]
        oauth = requests_oauthlib.OAuth1(**site["oauth"])
        category_id = int(site["sale_category_id"])
        add_options_count = 0
        current_page_num = 1
        error_count = 0
        while error_count < 10:
            get_products_response = get_products(oauth, site_url, current_page_num)
            if get_products_response.status_code != 200:
                if error_count == 0:
                    print()
                try:
                    print(f"[{datetime.datetime.now()}] {get_products_response.json()}")
                except:
                    pass
                error_count += 1
                current_page_num += 1
                continue
            error_count = 0
            try:
                for _, product_value in get_products_response.json()["success"]["goods_list"].items():
                    add_options_count += 1
                    if int(product_value["entry_cat"]["id"]) == category_id:
                        if "addpopular" in str(product_value["entry_description"]):
                            addcategory_id = site["popular_category_id"]
                        else:
                            addcategory_id = ""
                        try:
                            print(f'\r[{site_url}] {add_options_count}: {edit_product(oauth, site_url, category_id, product_value["entry_id"], addcategory_id).json()}', end="")
                        except:
                            pass
            except:
                break
            current_page_num += 1
    print(f"[{datetime.datetime.now()}] Edit complite!")
    time.sleep(5)

def delete_product(oauth: requests_oauthlib.OAuth1, site_url, product_id):
    edit_product_url = f"https://{site_url}/uapi/shop/editgoods"
    data = {
        "method": "delete",
        "id": product_id,
    }
    return requests.post(edit_product_url, data=data, auth=oauth)

def delete_products(config):
    for site in config["sites"]:
        site_url = site["url"]
        oauth = requests_oauthlib.OAuth1(**site["oauth"])
        current_page_num = 1
        error_count = 0
        product_counter = 0
        while error_count < 10:
            get_products_response = get_products(oauth, site_url, current_page_num)
            if get_products_response.status_code != 200:
                if error_count == 0:
                    print()
                try:
                    print(get_products_response.json())
                except:
                    pass
                if error_count % 2 != 0:
                    current_page_num += 1
                error_count += 1
                continue
            error_count = 0
            try:
                sale_product = False
                for _, product_value in get_products_response.json()["success"]["goods_list"].items():
                    if int(product_value["entry_cat"]["id"]) == int(site["sale_category_id"]):
                        product_counter += 1
                        sale_product = True
                        print(f'[{site_url}] {product_counter}: {delete_product(oauth, site_url, product_value["entry_id"]).json()}')
                if not sale_product:
                    current_page_num += 1
            except:
                break
    print(f"[{datetime.datetime.now()}] Delete Complite!")

def selenium_script_check(config, site_url, webdriver: selenium.webdriver.Chrome):
    try:
        webdriver.get(f"https://{site_url}/panel/?a=shop&l=excel")
        webdriver.find_element(By.CLASS_NAME, "uid-login").click()
        time.sleep(3)
        webdriver.switch_to.window(webdriver.window_handles[1])
        webdriver.find_element(By.ID, "uid_email").send_keys(config["username"])
        webdriver.find_element(By.ID, "uid_password").send_keys(config["password"])
        webdriver.find_element(By.CLASS_NAME, "uid-form-submit").click()
        webdriver.switch_to.window(webdriver.window_handles[0])
        time.sleep(5)
        webdriver.find_element(By.CLASS_NAME, "fancybox-item").click()
        webdriver.find_element(By.ID, "xls_conf_file").send_keys(f"{os.getcwd()}/ps.xlsx")
        webdriver.find_element(By.ID, "sbtpfupload").click()
        return True
    except Exception as exception:
        return exception

def xlsx_load(config):
    for site in config["sites"]:
        site_url = site["url"]
        print(f"[{datetime.datetime.now()}] XLSX Load Site: {site_url}")
        exception_count = 0
        while True:
            options = Options()
            options.add_argument('headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            webdriver = selenium.webdriver.Chrome(options=options)
            selenium_script_check_return = selenium_script_check(config, site_url, webdriver)
            if selenium_script_check_return:
                if exception_count < 10:
                    print()
                    for i in range(60):
                        print(f"\rTimer: {60 - i}    ", end="")
                        time.sleep(1)
                    print()
                    webdriver.find_element(By.ID, "sbtgprice").click()
                    for i in range(60):
                        print(f"\rTimer: {60 - i}    ", end="")
                        time.sleep(1)
                    print()
                    break
                else:
                    exit(1)
            else:
                exception_count += 1
                print(f"Selenium Exception! Count: {exception_count} \n{selenium_script_check_return}\n\nWait 10 minutes")
                time.sleep(10 * 60)
            webdriver.close()
    print(f"[{datetime.datetime.now()}] XLSX Load Complite!")

def refresh(config):
    for site in config["sites"]:
        site_url = site["url"]
        refresh_count = 0
        try:
            refresh_responce = requests.get(f"https://{site_url}/shop/telegram_shop/catalog", timeout=30).text
        except Exception as exception:
            print(exception)
        while refresh_count < 30 and refresh_responce.count("nf150.svg") > 1:
            try:
                requests.get(f"https://{site_url}/shop/all/", timeout=15)
                for i in range(2, 50):
                    requests.get(f"https://{site_url}/shop/all/{i}", timeout=15)
                refresh_responce = requests.get(f"https://{site_url}/shop/telegram_shop/catalog", timeout=30).text
            except Exception as exception:
                print(exception)
            print(f"\r[{site_url}] Refresh count: {refresh_count + 1}")
            refresh_count += 1
    print(f"[{datetime.datetime.now()}] Refresh complite!")

def auto(config, products_count):
    parser(config, products_count)
    delete_products(config)
    xlsx_load(config)
    edit_products(config)
    refresh(config)
    last_update = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    read_file = open("config.json", "r")
    current_config = json.load(read_file)
    read_file.close()
    current_config["_last_update"] = last_update
    current_config["_first_end_time"] = first_end_time
    write_file = open("config.json", "w")
    json.dump(current_config, write_file, indent=4)
    write_file.close()
    print(f"[{datetime.datetime.now()}] Auto complite! {last_update}")
    print(f'First End Discount Date: {datetime.datetime.fromtimestamp(first_end_time).strftime("%d.%m.%Y")}')
    time.sleep(5)

def set_proxy(config):
    global proxy
    proxies = config["proxies"]
    for current_proxy in proxies:
        try:
            response = requests.get("https://store.playstation.com", proxies={"http": current_proxy, "https": current_proxy}, timeout=20).text
            if "access denied" not in response.lower():
                proxy = current_proxy
                print(f"[{datetime.datetime.now()}] Proxy: {current_proxy}")
                time.sleep(2)
                return
            time.sleep(2)
        except:
            pass
    print(f"[{datetime.datetime.now()}] All Proxies Banned!")

def main():
    config_file = open("config.json")
    config = json.load(config_file)
    config_file.close()
    print()
    for site in config["sites"]:
        print(f"Site: {site['url']}")
    set_proxy(config)
    if "hour_rate" in config:
        hour_rate = int(config["hour_rate"])
    else:
        hour_rate = 6
    products_count = int(config["products_count"])
    mode = config["default_mode"]
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    if len(sys.argv) > 2:
        products_count = int(sys.argv[2])
    print(f"Mode: {mode}\nProducts Count: {products_count}\nHour Rate: {hour_rate}")
    match mode:
        case "parser":
            parser(config, products_count)
        case "edit":
            edit_products(config)
        case "auto":
            first_flag = True
            previous_hour = -1
            while True:
                now = datetime.datetime.now()
                # print(now.date(), datetime.datetime.fromtimestamp(int(config["_first_end_time"])).date(), now.hour, hour_rate, previous_hour)
                if first_flag or (now.hour != previous_hour and now.hour % hour_rate == 0 and datetime.datetime.fromtimestamp(int(config["_first_end_time"])).date() == now.date()):
                    if not first_flag:
                        config_file = open("config.json")
                        config = json.load(config_file)
                        config_file.close()
                        print(json.dumps(config, indent=4))
                    if hour_rate < 24 or hour_rate > 1:
                        previous_hour = now.hour
                    first_flag = False
                    auto(config, products_count)
                else:
                    time.sleep(10 * 60)

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    main()