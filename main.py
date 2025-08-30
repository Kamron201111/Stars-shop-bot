
import telebot
from telebot.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
import json

TOKEN = "7549045887:AAEsCx_I4oRsAebCPfpa9bNf8nbZPc8w9X0"
PROVIDER_TOKEN = "" # Do Not Edit
bot = telebot.TeleBot(TOKEN)
MEMBERS_FILE = 'members.json'
CHANNELS_FILE = 'channels.json'
PRODUCTS_FILE = 'products.json'
admin_id = 7538420552 #put your id here
ADMIN_USER_IDS = [admin_id]
banned_users = []
is_bot_active = True


def load_users_from_file():
    try:
        with open(MEMBERS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def broadcast_message(message):
    broadcast_list = load_users_from_file()
    total_users = len(broadcast_list)
    successful_sends = 0
    failed_sends = 0

    
    status_message = bot.send_message(
        admin_id, 
        f"بدء الإرسال:\nتم الإرسال بنجاح: {successful_sends}\nالأخطاء: {failed_sends}\nالإجمالي: {total_users}"
    )

    for user_id in broadcast_list:
        try:
            bot.send_message(user_id, message)
            successful_sends += 1
        except Exception:
            failed_sends += 1
        
        
        bot.edit_message_text(
            chat_id=admin_id,
            message_id=status_message.message_id,
            text=f"الإرسال قيد التنفيذ:\nتم الإرسال بنجاح: {successful_sends}\nالأخطاء: {failed_sends}\nالإجمالي: {total_users}"
        )
    

    bot.send_message(
        admin_id, 
        f"تم الإرسال:\nتم الإرسال بنجاح: {successful_sends}\nالأخطاء: {failed_sends}\nالإجمالي: {total_users}"
    )
def is_admin(user_id):
    return user_id in ADMIN_USER_IDS

def is_user_subscribed(user_id):
    try:
        with open(CHANNELS_FILE, "r") as f:
            channels = json.load(f)
    except FileNotFoundError:
        channels = []

    for channel in channels:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def get_subscription_markup():
    try:
        with open(CHANNELS_FILE, "r") as f:
            channels = json.load(f)
    except FileNotFoundError:
        channels = []

    markup = InlineKeyboardMarkup()
    for channel in channels:
    	ch = channel.replace('@', '')
    	markup.add(InlineKeyboardButton(f"اشترك في {channel}", url=f"https://t.me/{ch}"))
    	markup.add(InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_subscription"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    if is_user_subscribed(call.from_user.id):
        bot.send_message(call.message.chat.id, "تم التحقق من اشتراكك بنجاح!")
        send_welcome(call.message)
    else:
        bot.send_message(call.message.chat.id, "يجب الاشتراك في جميع القنوات لاستخدام البوت.")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    if not is_bot_active:
        bot.send_message(message.chat.id, "البوت متوقف مؤقتًا الآن. يرجى المحاولة لاحقًا.")
        return
    
    if message.from_user.id in banned_users:
        bot.send_message(message.chat.id, "أنت محظور من استخدام هذا البوت.")
        return

    
    if not is_user_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "يجب عليك الاشتراك في القنوات التالية لاستخدام البوت:",
            reply_markup=get_subscription_markup()
        )
        return

    
    try:
        with open(MEMBERS_FILE, "r") as f:
            members = json.load(f)
    except FileNotFoundError:
        members = []

    if message.from_user.id not in members:
        members.append(message.from_user.id)
        with open(MEMBERS_FILE, "w") as f:
            json.dump(members, f)

    
    bot.send_message(
        message.chat.id,
        "مرحبًا! استخدم الأزرار أدناه للتفاعل مع البوت.",
        reply_markup=main_menu()
    )


def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("راسل المطور", url="https://t.me/dj_8s"),
        InlineKeyboardButton("شراء الملفات", callback_data="list_products")
    )
    return markup
@bot.callback_query_handler(func=lambda call: call.data == "list_products")
def list_products(call):
    with open('products.json', 'r') as f:
        products = json.load(f)

    if not products:
        bot.send_message(call.message.chat.id, "لا توجد منتجات متاحة حاليًا.")
        return

    markup = InlineKeyboardMarkup()
    markup.add(
   
        InlineKeyboardButton(f"اسم الملف", callback_data=f"no"),
        InlineKeyboardButton(f"سعر الملف", callback_data=f"no"),
        InlineKeyboardButton(f"لغه الملف", callback_data=f"no"), 
        )
    for product in products:
        markup.add(
            InlineKeyboardButton(f" {product['name']}", callback_data=f"product_{product['name']}"),
            InlineKeyboardButton(f" {product['price']} نجمة", callback_data=f"product_{product['name']}"),
            InlineKeyboardButton(f" {product['language']}", callback_data=f"product_{product['name']}")
            )
            
    
    bot.send_message(call.message.chat.id, '''       مرحبا بك في قسم شراء الملفات.
    هنا هتلاقي اي ملف مدفوع وبسعر رمزي جدا (مش عارف مين رمزي بس هما بيقولو كدا)
                             ''', reply_markup=markup)
  
@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def product_details(call):
    product_name = call.data.split("_")[1]
    with open('products.json', 'r') as f:
        products = json.load(f)

    product = next((p for p in products if p['name'] == product_name), None)
    if product:
        bot.send_message(
            call.message.chat.id,
            f"اسم الملف: {product['name']}\n"
            f"الوصف: {product['description']}\n"
            f"السعر: {product['price']} نجمة\n"
            f"اللغة: {product['language']}\n",
            reply_markup=product_menu(product['name'])
        )

def product_menu(product_name):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("شراء", callback_data=f"buy_{product_name}"),
        InlineKeyboardButton("رجوع", callback_data="list_products")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_payment(call):
    product_name = call.data.split("_")[1]
    with open('products.json', 'r') as f:
        products = json.load(f)


    product = next((p for p in products if p['name'] == product_name), None)
    if product:
        prices = [LabeledPrice(label=product['name'], amount=product['price'])] 

        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=product['name'],
            description=product['description'],
            provider_token=PROVIDER_TOKEN,
            currency="XTR",  
            prices=prices,
            start_parameter="pay_with_stars",
            invoice_payload=f"Star-Payment-{product_name}",
        )

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout_handler(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


def successful_payment(message):
    payload = message.successful_payment.invoice_payload
    product_name = payload.split("-")[-1]
    
 
    product = get_product_details(product_name)
    
    
    if product:
        notify_owner(message.from_user.username, product)
    
    send_product_file(message, product_name)

def send_product_file(message, product_name):
    with open('products.json', 'r') as f:
        products = json.load(f)
    
    product = next((p for p in products if p['name'] == product_name), None)
    if product and 'file_path' in product:
        file_path = product['file_path']
        
        
        if os.path.exists(file_path):
            bot.send_message(message.chat.id, "تم الدفع بنجاح! شكرًا لاستخدامك الخدمة.")
            bot.send_document(message.chat.id, open(file_path, 'rb'))
        else:
            bot.send_message(message.chat.id, "حدث خطأ، الملف غير موجود.")
    else:
        bot.send_message(message.chat.id, "حدث خطأ، لم يتم العثور على الملف المطلوب.")

def notify_owner(username, product):
    message = (
        f"قام المستخدم @{username} بشراء التالي:\n"
        f"اسم الملف: {product['name']}\n"
        f"الوصف: {product['description']}\n"
        f"السعر: {product['price']} نجمة\n"
        f"اللغة: {product['language']}\n"
    )
    bot.send_message(admin_id, message)

def get_product_details(product_name):
    with open('products.json', 'r') as f:
        products = json.load(f)
    
    return next((p for p in products if p['name'] == product_name), None)
def update_sales_count(product_name):
    try:
        
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)

        
        for product in products:
            if product['name'] == product_name:
                product['sales_count'] = product.get('sales_count', 0) + 1
                break

       
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products, f, ensure_ascii=False, indent=4)

    except FileNotFoundError:
        print("ملف المنتجات غير موجود.")
    except Exception as e:
        print(f"حدث خطأ أثناء تحديث المبيعات: {e}")

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    try:
        
        payload = message.successful_payment.invoice_payload
        product_name = payload.split("-")[-1]

        
        update_sales_count(product_name)

        
        send_product_file(message, product_name)

        
        bot.send_message(message.chat.id, "تم الدفع بنجاح! شكراً لك.")
    except Exception as e:
        bot.send_message(message.chat.id, "حدث خطأ أثناء معالجة الدفع.")
        print(f"خطأ في الدفع الناجح: {e}")

    
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "عذرًا، هذه الميزة مخصصة للإدارة فقط.")
        return

    markup = InlineKeyboardMarkup(row_width=2)

    
    markup.add(
        InlineKeyboardButton("قفل البوت", callback_data="shutdown_bot"),
        InlineKeyboardButton("فتح البوت", callback_data="start_bot")
    )

   
    markup.add(
        InlineKeyboardButton("تحكم بالأعضاء", callback_data="manage_members")
    )

    
    markup.add(
        InlineKeyboardButton("تحكم بالمنتجات", callback_data="manage_products")
    )

    
    markup.add(
        InlineKeyboardButton("الإحصائيات", callback_data="show_stats")
    )

    bot.send_message(message.chat.id, "لوحة الإدارة:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "manage_members")
def manage_members(call):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("إضافة قناة اشتراك", callback_data="add_channel"),
        InlineKeyboardButton("إزالة قناة اشتراك", callback_data="remove_channel"),
        InlineKeyboardButton("عرض قنوات الاشتراك", callback_data="list_channels"))
    markup.add(
        InlineKeyboardButton("حظر عضو", callback_data="ban_user"),
        InlineKeyboardButton("إلغاء حظر عضو", callback_data="unban_user"),
        )
    markup.add(
        InlineKeyboardButton("رفع أدمن", callback_data="promote_admin"),
        InlineKeyboardButton("تنزيل أدمن", callback_data="demote_admin"),
        )
    markup.add(
        InlineKeyboardButton("أذاعه", callback_data="broadcast_message")
    )
    markup.add(InlineKeyboardButton("رجوع", callback_data="admin_panel"))
    bot.edit_message_text("تحكم بالأعضاء:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    
@bot.callback_query_handler(func=lambda call: call.data == "broadcast_message")
def handle_broadcast_message(call):
    user_id = call.from_user.id
    msg = bot.send_message(user_id, "أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:")
    bot.register_next_step_handler(msg, send_broadcast)


def send_broadcast(message):
    broadcast_message(message.text)
    bot.send_message(message.chat.id, "تم إرسال الرسالة بنجاح!")

@bot.callback_query_handler(func=lambda call: call.data == "manage_products")
def manage_products(call):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("إضافة منتج", callback_data="add_product"),
        InlineKeyboardButton("حذف منتج", callback_data="remove_product"),
        )
    markup.add(
        InlineKeyboardButton("تعديل منتج", callback_data="edit_product"),
        InlineKeyboardButton("إضافة تخفيض", callback_data="add_discount")
    )
    markup.add(InlineKeyboardButton("رجوع", callback_data="admin_panel"))
    bot.edit_message_text("تحكم بالمنتجات:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def return_to_admin_panel(call):
    if is_admin(call.from_user.id):  
        markup = InlineKeyboardMarkup(row_width=2)

        
        markup.add(
            InlineKeyboardButton("قفل البوت", callback_data="shutdown_bot"),
            InlineKeyboardButton("فتح البوت", callback_data="start_bot")
        )

        
        markup.add(
            InlineKeyboardButton("تحكم بالأعضاء", callback_data="manage_members")
        )

        
        markup.add(
            InlineKeyboardButton("تحكم بالمنتجات", callback_data="manage_products")
        )

        
        markup.add(
            InlineKeyboardButton("الإحصائيات", callback_data="show_stats")
        )

        bot.edit_message_text("لوحة الإدارة:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "عذرًا، هذه الميزة مخصصة للإدارة فقط.")



@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def add_channel(call):
    msg = bot.send_message(call.message.chat.id, "أرسل معرف القناة")
    bot.register_next_step_handler(msg, process_add_channel)

def process_add_channel(message):
    try:
        channel = message.text
        
        
        if not channel.startswith('@'):
            channel = '@' + channel
        
        with open(CHANNELS_FILE, "r") as f:
            channels = json.load(f)
    except FileNotFoundError:
        channels = []

    if channel not in channels:
        channels.append(channel)
        with open(CHANNELS_FILE, "w") as f:
            json.dump(channels, f, ensure_ascii=False, indent=4)
        bot.send_message(message.chat.id, f"تمت إضافة القناة {channel} إلى قائمة الاشتراكات الإلزامية.")
    else:
        bot.send_message(message.chat.id, "القناة موجودة بالفعل في القائمة.")


@bot.callback_query_handler(func=lambda call: call.data == "remove_channel")
def remove_channel(call):
    msg = bot.send_message(call.message.chat.id, "أرسل معرف القناة ")
    bot.register_next_step_handler(msg, process_remove_channel)

def process_remove_channel(message):
    try:
        channel = message.text
        if not channel.startswith('@'):
            channel = '@' + channel
        with open(CHANNELS_FILE, "r") as f:
            channels = json.load(f)
    except FileNotFoundError:
        channels = []

    if channel in channels:
        channels.remove(channel)
        with open(CHANNELS_FILE, "w") as f:
            json.dump(channels, f, ensure_ascii=False, indent=4)
        bot.send_message(message.chat.id, f"تمت إزالة القناة {channel} من قائمة الاشتراكات الإلزامية.")
    else:
        bot.send_message(message.chat.id, "القناة غير موجودة في القائمة.")

@bot.callback_query_handler(func=lambda call: call.data == "list_channels")
def list_channels(call):
    try:
        with open(CHANNELS_FILE, "r") as f:
            channels = json.load(f)
    except FileNotFoundError:
        channels = []

    if channels:
        bot.send_message(call.message.chat.id, "قنوات الاشتراك الإلزامية:\n" + "\n".join(channels))

    else:
        bot.send_message(call.message.chat.id, "لا توجد قنوات اشتراك إلزامية حالياً.")
        
@bot.callback_query_handler(func=lambda call: call.data == "shutdown_bot")
def shutdown_bot(call):
    global is_bot_active
    is_bot_active = False
    bot.send_message(call.message.chat.id, "تم قفل البوت.")

@bot.callback_query_handler(func=lambda call: call.data == "start_bot")
def start_bot(call):
    global is_bot_active
    is_bot_active = True
    bot.send_message(call.message.chat.id, "تم فتح البوت.")

@bot.callback_query_handler(func=lambda call: call.data == "promote_admin")
def promote_admin(call):
    msg = bot.send_message(call.message.chat.id, "أرسل ID العضو لترقيته كأدمن:")
    bot.register_next_step_handler(msg, add_admin)

def add_admin(message):
    try:
        user_id = int(message.text)
        if user_id not in ADMIN_USER_IDS:
            ADMIN_USER_IDS.append(user_id)
            bot.send_message(message.chat.id, f"تمت ترقية {user_id} كأدمن.")
        else:
            bot.send_message(message.chat.id, "المستخدم بالفعل أدمن.")
    except ValueError:
        bot.send_message(message.chat.id, "ID غير صالح.")

@bot.callback_query_handler(func=lambda call: call.data == "demote_admin")
def demote_admin(call):
    msg = bot.send_message(call.message.chat.id, "أرسل ID العضو لإزالته من قائمة الأدمن:")
    bot.register_next_step_handler(msg, remove_admin)

def remove_admin(message):
    try:
        user_id = int(message.text)
        if user_id in ADMIN_USER_IDS:
            ADMIN_USER_IDS.remove(user_id)
            bot.send_message(message.chat.id, f"تمت إزالة {user_id} من قائمة الأدمن.")
        else:
            bot.send_message(message.chat.id, "المستخدم ليس أدمن.")
    except ValueError:
        bot.send_message(message.chat.id, "ID غير صالح.")

@bot.callback_query_handler(func=lambda call: call.data == "ban_user")
def ban_user(call):
    msg = bot.send_message(call.message.chat.id, "أرسل ID العضو لحظره:")
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    try:
        user_id = int(message.text)
        if user_id not in banned_users:
            banned_users.append(user_id)
            bot.send_message(message.chat.id, f"تم حظر المستخدم {user_id}.")
        else:
            bot.send_message(message.chat.id, "المستخدم محظور بالفعل.")
    except ValueError:
        bot.send_message(message.chat.id, "ID غير صالح.")

@bot.callback_query_handler(func=lambda call: call.data == "unban_user")
def unban_user(call):
    msg = bot.send_message(call.message.chat.id, "أرسل ID العضو لإلغاء حظره:")
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    try:
        user_id = int(message.text)
        if user_id in banned_users:
            banned_users.remove(user_id)
            bot.send_message(message.chat.id, f"تم إلغاء حظر المستخدم {user_id}.")
        else:
            bot.send_message(message.chat.id, "المستخدم غير محظور.")
    except ValueError:
        bot.send_message(message.chat.id, "ID غير صالح.")


@bot.callback_query_handler(func=lambda call: call.data == "add_product")
def add_product(call):
    msg = bot.send_message(call.message.chat.id, "أرسل اسم الملف:")
    bot.register_next_step_handler(msg, process_add_product)

def process_add_product(message):
    product = {"name": message.text}
    msg = bot.send_message(message.chat.id, "أرسل وصف الملف:")
    bot.register_next_step_handler(msg, lambda m: add_product_description(m, product))

def add_product_description(message, product):
    product["description"] = message.text
    msg = bot.send_message(message.chat.id, "أرسل سعر الملف بالنجوم:")
    bot.register_next_step_handler(msg, lambda m: add_product_price(m, product))

def add_product_price(message, product):
    try:
        product["price"] = int(message.text)
        msg = bot.send_message(message.chat.id, "أرسل الملف المرفق:")
        bot.register_next_step_handler(msg, lambda m: add_product_file(m, product))
    except ValueError:
        bot.send_message(message.chat.id, "سعر غير صالح. حاول مرة أخرى.")

if not os.path.exists('documents'):
    os.makedirs('documents')

def add_product_file(message, product):
    if message.document:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        file_path = f'documents/{message.document.file_name}'
        

        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        product["file_path"] = file_path
        
        msg = bot.send_message(message.chat.id, "أدخل لغة الملف:")
        bot.register_next_step_handler(msg, lambda m: add_product_language(m, product))
    else:
        bot.send_message(message.chat.id, "لم يتم إرسال ملف. حاول مرة أخرى.")
        
def add_product_language(message, product):
    product["language"] = message.text
    product["sales_count"] = 0  

    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
            if isinstance(products, dict):
                products = []
    except FileNotFoundError:
        products = []

    products.append(product)

    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    bot.send_message(message.chat.id, "تم إضافة الملف بنجاح.")


@bot.callback_query_handler(func=lambda call: call.data == "show_stats")
def show_stats(call):
    stats_message = get_stats()
    bot.send_message(call.message.chat.id, stats_message)

def get_stats():
    try:
        with open(MEMBERS_FILE, 'r') as f:
            members = json.load(f)
            total_members = len(members)
    except FileNotFoundError:
        total_members = 0

    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
    except FileNotFoundError:
        products = []

    stats_message = f"عدد الأعضاء: {total_members}\n"
    stats_message += "إحصائيات المبيعات لكل ملف:\n"
    for product in products:
        stats_message += f"{product['name']}: {product.get('sales_count', 0)} مرة\n"
    
    return stats_message

import threading
import time


@bot.callback_query_handler(func=lambda call: call.data == "add_discount")
def discount_product(call):
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
    except FileNotFoundError:
        products = []

    if not products:
        bot.send_message(call.message.chat.id, "لا توجد منتجات متاحة للتخفيض.")
        return

    markup = InlineKeyboardMarkup()
    for product in products:
        markup.add(InlineKeyboardButton(product['name'], callback_data=f"discount_{product['name']}"))
    bot.send_message(call.message.chat.id, "اختر المنتج لإضافة التخفيض:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("discount_"))
def apply_discount(call):
    product_name = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, "أدخل السعر الجديد أثناء فترة التخفيض:")
    bot.register_next_step_handler(msg, lambda m: set_discount_price(m, product_name))

def set_discount_price(message, product_name):
    try:
        new_price = int(message.text)
        msg = bot.send_message(message.chat.id, "أدخل مدة التخفيض (بالدقائق):")
        bot.register_next_step_handler(msg, lambda m: set_discount_duration(m, product_name, new_price))
    except ValueError:
        bot.send_message(message.chat.id, "السعر غير صالح. حاول مرة أخرى.")

def set_discount_duration(message, product_name, new_price):
    try:
        duration = int(message.text)
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)

        product = next((p for p in products if p['name'] == product_name), None)
        if product:
            old_price = product['price']
            product['price'] = new_price
            product['discount_duration'] = duration
            product['old_price'] = old_price

            with open(PRODUCTS_FILE, 'w') as f:
                json.dump(products, f, ensure_ascii=False, indent=4)

            bot.send_message(message.chat.id, f"تم إضافة التخفيض للمنتج {product_name}. السعر الجديد: {new_price} لمدة {duration} دقيقة.")

            
            threading.Thread(target=reset_price, args=(product_name, old_price, duration)).start()
        else:
            bot.send_message(message.chat.id, "لم يتم العثور على المنتج.")
    except ValueError:
        bot.send_message(message.chat.id, "المدة غير صالحة. حاول مرة أخرى.")

def reset_price(product_name, old_price, duration):
    time.sleep(duration * 60)
    with open(PRODUCTS_FILE, 'r') as f:
        products = json.load(f)

    product = next((p for p in products if p['name'] == product_name), None)
    if product:
        product['price'] = old_price
        product.pop('discount_duration', None)
        product.pop('old_price', None)

        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products, f, ensure_ascii=False, indent=4)


@bot.callback_query_handler(func=lambda call: call.data == "edit_product")
def edit_product(call):
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
    except FileNotFoundError:
        products = []

    if not products:
        bot.send_message(call.message.chat.id, "لا توجد منتجات متاحة للتعديل.")
        return

    markup = InlineKeyboardMarkup()
    for product in products:
        markup.add(InlineKeyboardButton(product['name'], callback_data=f"edt_{product['name']}"))
    bot.send_message(call.message.chat.id, "اختر المنتج للتعديل:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edt_"))
def edit_product_options(call):
    product_name = call.data.split("_")[1]
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("تعديل الاسم", callback_data=f"edit_name_{product_name}"),
        InlineKeyboardButton("تعديل الوصف", callback_data=f"edit_desc_{product_name}"),
        InlineKeyboardButton("تعديل السعر", callback_data=f"edit_price_{product_name}"),
        InlineKeyboardButton("تعديل اللغة", callback_data=f"edit_lang_{product_name}"),
        InlineKeyboardButton("تغيير الملف", callback_data=f"edit_file_{product_name}")
    )
    bot.send_message(call.message.chat.id, "اختر ما تريد تعديله:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_name_"))
def edit_name(call):
    product_name = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, f"أدخل الاسم الجديد للمنتج '{product_name}':")
    bot.register_next_step_handler(msg, lambda m: update_product_field(m, product_name, "name"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_desc_"))
def edit_description(call):
    product_name = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, f"أدخل الوصف الجديد للمنتج '{product_name}':")
    bot.register_next_step_handler(msg, lambda m: update_product_field(m, product_name, "description"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price_"))
def edit_price(call):
    product_name = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, f"أدخل السعر الجديد للمنتج '{product_name}':")
    bot.register_next_step_handler(msg, lambda m: update_product_field(m, product_name, "price"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_lang_"))
def edit_language(call):
    product_name = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, f"أدخل اللغة الجديدة للمنتج '{product_name}':")
    bot.register_next_step_handler(msg, lambda m: update_product_field(m, product_name, "language"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_file_"))
def edit_file(call):
    product_name = call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, f"أرسل الملف الجديد للمنتج '{product_name}':")
    bot.register_next_step_handler(msg, lambda m: update_product_file(m, product_name))

def update_product_field(message, product_name, field):
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)

        product = next((p for p in products if p['name'] == product_name), None)
        if product:
            if field == "price":
                product[field] = int(message.text)
            else:
                product[field] = message.text

            with open(PRODUCTS_FILE, 'w') as f:
                json.dump(products, f, ensure_ascii=False, indent=4)

            bot.send_message(message.chat.id, f"تم تحديث {field} بنجاح.")
        else:
            bot.send_message(message.chat.id, "لم يتم العثور على المنتج.")
    except ValueError:
        bot.send_message(message.chat.id, "القيمة المدخلة غير صالحة.")
    except Exception as e:
        bot.send_message(message.chat.id, "حدث خطأ أثناء التعديل.")

def update_product_file(message, product_name):
    if message.document:
        try:
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            file_path = f'documents/{message.document.file_name}'
            
            downloaded_file = bot.download_file(file_info.file_path)
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            with open(PRODUCTS_FILE, 'r') as f:
                products = json.load(f)

            product = next((p for p in products if p['name'] == product_name), None)
            if product:
                old_file_path = product.get("file_path")
                if old_file_path and os.path.exists(old_file_path):
                    os.remove(old_file_path)
                
                product["file_path"] = file_path
                with open(PRODUCTS_FILE, 'w') as f:
                    json.dump(products, f, ensure_ascii=False, indent=4)

                bot.send_message(message.chat.id, "تم تحديث الملف بنجاح.")
            else:
                bot.send_message(message.chat.id, "لم يتم العثور على المنتج.")
        except Exception as e:
            bot.send_message(message.chat.id, "حدث خطأ أثناء تحديث الملف.")
    else:
        bot.send_message(message.chat.id, "لم يتم إرسال ملف.")


@bot.callback_query_handler(func=lambda call: call.data == "remove_product")
def remove_product(call):
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)
    except FileNotFoundError:
        products = []

    if not products:
        bot.send_message(call.message.chat.id, "لا توجد منتجات متاحة للحذف.")
        return

    markup = InlineKeyboardMarkup()
    for product in products:
        markup.add(InlineKeyboardButton(product['name'], callback_data=f"remove_{product['name']}"))
    bot.send_message(call.message.chat.id, "اختر المنتج للحذف:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_"))
def confirm_remove_product(call):
    product_name = call.data.split("_")[1]
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("تأكيد", callback_data=f"confirm_remove_{product_name}"),
        InlineKeyboardButton("رجوع", callback_data="admin_panel")
    )
    bot.send_message(call.message.chat.id, f"هل تريد حذف المنتج {product_name}؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_remove_"))
def delete_product(call):
    product_name = call.data.split("_")[2]
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            products = json.load(f)

        product = next((p for p in products if p['name'] == product_name), None)
        if product:
            products.remove(product)
            if 'file_path' in product and os.path.exists(product['file_path']):
                os.remove(product['file_path'])
            with open(PRODUCTS_FILE, 'w') as f:
                json.dump(products, f, ensure_ascii=False, indent=4)
            bot.send_message(call.message.chat.id, f"تم حذف المنتج {product_name} بنجاح.")
        else:
            bot.send_message(call.message.chat.id, "لم يتم العثور على المنتج.")
    except Exception as e:
        bot.send_message(call.message.chat.id, "حدث خطأ أثناء الحذف.")

bot.infinity_polling()
