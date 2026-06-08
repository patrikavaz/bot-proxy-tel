# 📡 MTProto Proxy Bot

ربات تلگرام که هر ۱۲ ساعت لیست پروکسی‌های MTProto را برای همه کاربران ثبت‌شده ارسال می‌کند.

## دستورات ربات

| دستور | عملکرد |
|-------|---------|
| `/start` | ثبت‌نام و شروع دریافت آپدیت‌ها |
| `/proxies` | دریافت فوری لیست پروکسی‌ها |
| `/stop` | لغو اشتراک |
| `/stats` | تعداد کاربران ثبت‌شده |

---

## معماری پروژه

```
your-repo/
├── .github/
│   └── workflows/
│       └── broadcast.yml   ← هر ۱۲ ساعت برای همه ارسال می‌کند
├── bot.py                  ← کد اصلی ربات
├── requirements.txt
├── Procfile                ← برای Railway
└── .gitignore
```

---

## راه‌اندازی

### مرحله ۱ — ساخت ربات تلگرام
1. به [@BotFather](https://t.me/BotFather) پیام بده
2. `/newbot` بفرست و توکن را کپی کن

### مرحله ۲ — دیپلوی روی Railway (رایگان)

ربات باید دائماً روشن باشد تا `/start` کاربران را دریافت کند.

1. برو به [railway.app](https://railway.app) و با GitHub لاگین کن
2. **New Project** → **Deploy from GitHub repo** → repo خود را انتخاب کن
3. در بخش **Variables** این متغیر را اضافه کن:
   - `TELEGRAM_TOKEN` = توکن ربات

✅ Railway خودکار `Procfile` را می‌خواند و ربات را روشن می‌کند.

### مرحله ۳ — GitHub Secrets برای Broadcast

1. برو به repo → **Settings** → **Secrets and variables** → **Actions**
2. اضافه کن:
   - `TELEGRAM_TOKEN` = توکن ربات

### مرحله ۴ — تست

1. ربات را در تلگرام پیدا کن و `/start` بزن
2. برو به **Actions** → **Proxy Broadcast** → **Run workflow**
3. باید پیام دریافت کنی ✅

---

## نکات مهم

- **Railway**: ربات را دائماً روشن نگه می‌دارد (رایگان تا ۵۰۰ ساعت در ماه)
- **GitHub Actions**: هر ۱۲ ساعت broadcast می‌کند
- **users.json**: لیست کاربران به عنوان artifact در GitHub ذخیره می‌شود
