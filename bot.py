import logging
import asyncio
import traceback
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# SELENIUM LIBS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoAlertPresentException

# TELEGRAM LIBS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ================= CONFIGURATION =================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
try:
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_ID").split(',')]
except:
    ADMIN_IDS = []

# === 555Mix Configuration ===
PANEL_CONFIG = {
    6: { "name": "Senior Panel", "url": "https://sm.bet555mix.com/", "user": "uu2", "pass": os.getenv("MIX_SENIOR_PASS"), "menu": "Master" },
    9: { "name": "Master Panel", "url": "https://ms.bet555mix.com/", "user": "uu2yhp", "pass": os.getenv("MIX_MASTER_PASS"), "menu": "Agents" },
    12: { "name": "Agent Panel", "url": "https://ag.bet555mix.com/", "user": "uu2yhpabc", "pass": os.getenv("MIX_AGENT_PASS"), "menu": "Members" }
}

# === Credentials ===
SXZ_LOGIN_URL = "https://ag.sportsxzone.com/"
SXZ_PAYMENT_URL = "https://ag.sportsxzone.com/payment/deposit-withdrawl"
SXZ_ADMIN_USER = os.getenv("SXZ_USER")
SXZ_ADMIN_PASS = os.getenv("SXZ_PASS")

IBET_LOGIN_URL = "https://ag.ibet789.com/"
IBET_PAYMENT_URL = "https://ag.ibet789.com/_Part/Payment.aspx?pg=payment"
IBET_ADMIN_USER = os.getenv("IBET_USER")
IBET_ADMIN_PASS = os.getenv("IBET_PASS")

S899_LOGIN_URL = "https://ag.sports899.live/login"
S899_PAYMENT_URL = "https://ag.sports899.live/payment/deposit-withdraw"
S899_ADMIN_USER = os.getenv("S899_USER")
S899_ADMIN_PASS = os.getenv("S899_PASS")

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= HELPER FUNCTIONS =================
def get_next_receipt_id():
    """Generates sequential Receipt ID"""
    filename = "receipt_count.txt"
    if not os.path.exists(filename):
        with open(filename, "w") as f: f.write("0")
    
    with open(filename, "r") as f:
        current = int(f.read().strip())
    
    next_id = current + 1
    with open(filename, "w") as f:
        f.write(str(next_id))
    
    return f"{next_id:07d}"

def create_driver():
    """Starts Chrome Driver (On-Demand)"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--remote-allow-origins=*")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    return driver, wait

def safe_click(driver, element):
    try:
        ActionChains(driver).move_to_element(element).pause(0.2).click().perform()
    except:
        driver.execute_script("arguments[0].click();", element)

def take_error_screenshot(driver):
    try: driver.save_screenshot("error_log.png")
    except: pass

# ================= AGENT CLASSES =================
class SXZAgent:
    def process_transaction(self, username, amount, type="deposit"):
        driver, wait = None, None
        try:
            driver, wait = create_driver()
            # Login
            driver.get(SXZ_LOGIN_URL)
            time.sleep(2)
            if "payment" not in driver.current_url:
                try: wait.until(EC.element_to_be_clickable((By.XPATH, "//span[normalize-space()='Senior']"))).click()
                except: pass
                try:
                    wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Username'] | //input[@type='text']"))).send_keys(SXZ_ADMIN_USER)
                    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(SXZ_ADMIN_PASS)
                    driver.find_element(By.CSS_SELECTOR, "button.ant-btn-block").click()
                    time.sleep(5)
                except Exception as e: return f"❌ Login Error: {e}"

            # Payment
            driver.get(SXZ_PAYMENT_URL)
            time.sleep(2)
            try:
                search_input = wait.until(EC.element_to_be_clickable((By.ID, "advanced_search_userId")))
                driver.execute_script("arguments[0].value = '';", search_input)
                search_input.send_keys(username)
                time.sleep(1)
                search_input.send_keys(Keys.RETURN)
                try: wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-select-item-option-content"))).click()
                except: pass
            except: return "❌ Error: Search Box Not Found"
            time.sleep(2)

            final_amount = str(amount) if type == "deposit" else f"-{amount}"
            try:
                amount_box = wait.until(EC.presence_of_element_located((By.ID, "amount")))
                safe_click(driver, amount_box)
                driver.execute_script("arguments[0].value = '';", amount_box)
                amount_box.send_keys(final_amount)
            except: return "❌ Error: Amount Box Not Found"
            time.sleep(1)

            submit_btn = driver.find_element(By.CSS_SELECTOR, "button.w-100[type='submit']")
            safe_click(driver, submit_btn)
            time.sleep(2)
            try:
                confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.swal2-confirm")))
                safe_click(driver, confirm_btn)
            except: return "⚠️ Warning: Confirm Popup missing"
            
            time.sleep(3)
            return "SUCCESS"

        except Exception as e:
            take_error_screenshot(driver)
            return f"❌ SXZ Error: {str(e)}"
        finally:
            if driver: driver.quit()

class MixAgent:
    def manage_balance(self, target_username, amount, action_type="add"):
        driver, wait = None, None
        try:
            u_len = len(target_username)
            config = PANEL_CONFIG.get(u_len)
            if not config: return "❌ Invalid Username Length for Mix"

            driver, wait = create_driver()
            driver.get(config['url'])
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))).send_keys(config['user'])
                driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(config['pass'])
                driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(Keys.RETURN)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ant-layout-content")))
                time.sleep(2)
                try:
                    pops = driver.find_elements(By.XPATH, "//button[contains(., 'Agree') or contains(., 'AGREE') or contains(@class, 'ant-modal-close')]")
                    for p in pops: 
                        if p.is_displayed(): safe_click(driver, p)
                except: pass
            except Exception as e: return f"❌ Login Failed: {e}"

            menu_name = config['menu']
            if u_len == 6: driver.get("https://sm.bet555mix.com/masters")
            else:
                try:
                    menu_item = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{menu_name}')]")))
                    safe_click(driver, menu_item)
                    time.sleep(1)
                    list_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//li//span[text()='List'] | //a[contains(text(),'List')]")))
                    safe_click(driver, list_menu)
                except: pass
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.ant-table-row")))

            try:
                search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.ant-input")))
                driver.execute_script("arguments[0].value = '';", search_input)
                search_input.send_keys(target_username)
                search_input.send_keys(Keys.RETURN)
                time.sleep(2)
            except: return "❌ Search Box Error"

            try:
                user_row = wait.until(EC.presence_of_element_located((By.XPATH, f"//tr[contains(., '{target_username}')]")))
                try: safe_click(driver, user_row.find_element(By.CSS_SELECTOR, ".anticon-eye"))
                except: 
                    btns = user_row.find_elements(By.TAG_NAME, "button")
                    if btns: safe_click(driver, btns[-1])
            except: return f"❌ User {target_username} Not Found"
            time.sleep(1)

            manage_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Manage Balance')]")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", manage_btn)
            safe_click(driver, manage_btn)

            try: amount_box = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input.ant-input-number-input")))
            except: amount_box = driver.find_element(By.ID, "basic_amount")

            cmd_text = "add" if action_type == "add" else "remove"
            try:
                driver.execute_script("document.body.removeAttribute('aria-hidden');")
                radio = driver.find_element(By.XPATH, f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{cmd_text}')]")
                safe_click(driver, radio)
            except: pass

            amount_box.send_keys(str(amount))
            time.sleep(0.5)
            try: safe_click(driver, driver.find_element(By.XPATH, "//div[contains(@class, 'ant-modal-footer')]//button[contains(@class, 'ant-btn-primary')]"))
            except: amount_box.send_keys(Keys.ENTER)
            
            time.sleep(3)
            return "SUCCESS"

        except Exception as e:
            take_error_screenshot(driver)
            return f"❌ Mix Error: {str(e)}"
        finally:
            if driver: driver.quit()

class IBetAgent:
    def process_transaction(self, username, amount, type="deposit"):
        driver, wait = None, None
        try:
            driver, wait = create_driver()
            driver.get(IBET_LOGIN_URL)
            time.sleep(2)
            try:
                wait.until(EC.presence_of_element_located((By.ID, "txtUserName"))).send_keys(IBET_ADMIN_USER)
                try: driver.find_element(By.ID, "txtPassword").send_keys(IBET_ADMIN_PASS)
                except: driver.find_element(By.XPATH, "//input[@type='password']").send_keys(IBET_ADMIN_PASS)
                driver.find_element(By.ID, "btnSignIn").click()
                time.sleep(5)
            except Exception as e: return f"❌ Login Failed: {e}"

            driver.get(IBET_PAYMENT_URL)
            time.sleep(3)
            search_input = wait.until(EC.visibility_of_element_located((By.ID, "txtSearchUserName")))
            search_input.clear()
            search_input.send_keys(username)
            time.sleep(1)
            try: driver.find_element(By.ID, "btnSearch").click()
            except: driver.find_element(By.CLASS_NAME, "commandbutton").click()
            time.sleep(3)

            user_element = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[contains(text(), '{username}')] | //option[contains(text(), '{username}')] | //span[contains(text(), '{username}')]")))
            user_element.click()
            time.sleep(2)

            amount_input = wait.until(EC.visibility_of_element_located((By.ID, "ctl03_txtAmount")))
            final_amount = abs(int(amount))
            if type == "withdraw": final_amount = -final_amount
            amount_input.clear()
            amount_input.send_keys(str(final_amount))
            time.sleep(1)
            driver.find_element(By.ID, "ctl03_btnSave").click()
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                driver.switch_to.alert.accept()
            except: pass
            time.sleep(3)
            return "SUCCESS"

        except Exception as e:
            take_error_screenshot(driver)
            return f"❌ IBet Error: {str(e)}"
        finally:
            if driver: driver.quit()

class Sports899Agent:
    def process_transaction(self, username, amount, trans_type="deposit"):
        driver, wait = None, None
        try:
            driver, wait = create_driver()
            driver.get(S899_LOGIN_URL)
            try:
                code_in = wait.until(EC.visibility_of_element_located((By.ID, "code")))
                code_in.clear()
                code_in.send_keys(S899_ADMIN_USER)
                driver.find_element(By.ID, "password").send_keys(S899_ADMIN_PASS)
                driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]").click()
                time.sleep(5)
            except Exception as e: return f"❌ Login Failed: {e}"

            driver.get(S899_PAYMENT_URL)
            time.sleep(3)
            search_input = wait.until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Search...']")))
            search_input.clear()
            search_input.send_keys(username)
            time.sleep(1)
            search_input.send_keys(Keys.RETURN)
            time.sleep(2)

            user_el = wait.until(EC.element_to_be_clickable((By.XPATH, f"//option[contains(text(), '{username}')] | //li[contains(text(), '{username}')] | //span[normalize-space()='{username}']")))
            user_el.click()
            time.sleep(2)

            final_amount = abs(int(amount))
            if trans_type == "withdraw": final_amount = -final_amount 
            try:
                amount_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input.form-control.mb-2.p-2")))
                amount_input.clear()
                amount_input.send_keys(str(final_amount))
            except: return "❌ Amount Input Not Found"
            
            time.sleep(2)
            driver.find_element(By.XPATH, "//button[contains(@class, 'w-100') and contains(text(), 'Submit')]").click()
            time.sleep(2)
            try:
                confirm_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.swal2-confirm")))
                confirm_btn.click()
            except: pass
            time.sleep(2)
            return "SUCCESS"

        except Exception as e:
            take_error_screenshot(driver)
            return f"❌ S899 Error: {str(e)}"
        finally:
            if driver: driver.quit()

# ================= TELEGRAM HANDLERS =================
sxz_agent = SXZAgent()
mix_agent = MixAgent()
ibet_agent = IBetAgent()
s899_agent = Sports899Agent()

def restricted(func):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text(f"⛔ <b>Unauthorized</b>\nID: <code>{user_id}</code>", parse_mode="HTML")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Deposit", callback_data='deposit'), InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel')]
    ]
    text = (
        "🤖 <b>ALL-IN-ONE CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>Ready to Process:</b>\n"
        "• SportsXZone\n"
        "• 555Mix\n"
        "• IBet789\n"
        "• Sports899\n\n"
        "👇 <b>Select an action below:</b>"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'cancel':
        await query.edit_message_text("❌ <b>Action Cancelled</b>", parse_mode="HTML")
        context.user_data.clear()
        return

    context.user_data['action'] = query.data
    action_icon = "💰" if query.data == 'deposit' else "💸"
    
    await query.edit_message_text(
        f"{action_icon} <b>{query.data.upper()} SELECTED</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✍️ Reply format:\n"
        f"<code>username amount</code>\n\n"
        f"ℹ️ <i>Example:</i> <code>gg2mrc 50000</code>", 
        parse_mode="HTML"
    )

@restricted
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'action' not in context.user_data: return

    try:
        text = update.message.text.strip().split()
        if len(text) < 2:
            await update.message.reply_text("⚠️ <b>Invalid Format!</b>\nPlease use: <code>username amount</code>", parse_mode="HTML")
            return
        
        username, amount = text[0], text[1]
        action = context.user_data['action']
        u_lower = username.lower()
        u_upper = username.upper()

        # === 🔴 REVISED ROUTING LOGIC ===
        
        # 1. Sports899 (gg2)
        if u_lower.startswith("gg2"):
            system_name = "Sports899"
            is_s899 = True; is_mix = False; is_ibet = False; is_sxz = False
            
        # 2. IBet789 (APY)
        elif u_upper.startswith("APY"):
            system_name = "IBet789"
            is_s899 = False; is_mix = False; is_ibet = True; is_sxz = False

        # 3. SportsXZone (gy2 Override) - Force SXZ if starts with gy2
        elif u_lower.startswith("gy2"):
            system_name = "SportsXZone"
            is_s899 = False; is_mix = False; is_ibet = False; is_sxz = True

        # 4. 555Mix (Standard Prefixes OR Length)
        # Note: Added 'not starts with gy2' to be extra safe
        elif any(u_lower.startswith(p) for p in ["uu2", "aa1", "mm1"]) or (len(username) in [6, 9, 12] and not u_lower.startswith("gy2")):
            system_name = "555Mix"
            is_s899 = False; is_mix = True; is_ibet = False; is_sxz = False

        # 5. Default -> SportsXZone
        else:
            system_name = "SportsXZone"
            is_s899 = False; is_mix = False; is_ibet = False; is_sxz = True

        # === LOADING MESSAGE ===
        loading_text = (
            f"🔄 <b>Processing Transaction...</b>\n"
            f"⚙️ System: <b>{system_name}</b>\n"
            f"👤 User: <code>{username}</code>\n"
            f"⏳ <i>Connecting to server, please wait...</i>"
        )
        status_msg = await update.message.reply_text(loading_text, parse_mode="HTML")

        # === EXECUTE AGENT ===
        loop = asyncio.get_running_loop()
        result = ""
        
        if is_mix:
            mix_action = "add" if action == "deposit" else "remove"
            result = await loop.run_in_executor(None, mix_agent.manage_balance, username, amount, mix_action)
        elif is_ibet:
            result = await loop.run_in_executor(None, ibet_agent.process_transaction, username, amount, action)
        elif is_s899:
            result = await loop.run_in_executor(None, s899_agent.process_transaction, username, amount, action)
        else:
            # SXZ includes both "gy2" override and default fallback
            result = await loop.run_in_executor(None, sxz_agent.process_transaction, username, amount, action)

        # === FINAL RESULT ===
        if result == "SUCCESS":
            receipt_id = get_next_receipt_id()
            date_str = datetime.now().strftime("%d-%m-%Y %I:%M %p")
            formatted_amount = "{:,}".format(int(amount))
            
            success_text = (
                f"✅ <b>TRANSACTION SUCCESSFUL</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🧾 <b>Receipt No:</b> <code>{receipt_id}</code>\n"
                f"📅 <b>Date:</b> {date_str}\n\n"
                f"👤 <b>User:</b> <code>{username}</code>\n"
                f"💰 <b>Amount:</b> {formatted_amount}\n"
                f"🏦 <b>System:</b> {system_name}\n"
                f"🔄 <b>Type:</b> {action.upper()}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"✨ <i>Auto Processed by Bot</i>"
            )
            await status_msg.edit_text(success_text, parse_mode="HTML")
            
        elif "❌" in result and os.path.exists("error_log.png"):
            await status_msg.delete()
            await update.message.reply_photo(
                photo=open("error_log.png", "rb"), 
                caption=f"⚠️ <b>Transaction Failed</b>\n\n{result}", 
                parse_mode="HTML"
            )
            os.remove("error_log.png")
        else:
            await status_msg.edit_text(f"⚠️ <b>Error Occurred</b>\n\n{result}", parse_mode="HTML")

        context.user_data.clear()
        await asyncio.sleep(2)
        await start(update, context)

    except Exception as e:
        await update.message.reply_text(f"⚠️ <b>Bot Critical Error:</b>\n{e}", parse_mode="HTML")

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    print("🚀 Bot Started (Logic Updated)...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.run_polling()
