# PawLine Studio - חנות Etsy (קולקציית חג מולד, Line Art)

7 גזעים × 6 מוצרי POD = 42 מודעות, ועוד 3 מוצרים דיגיטליים.

## קבצים
| קובץ | מה עושה |
|---|---|
| `catalog.py` | מגדיר גזעים, מוצרים ומחירים ומייצר `listings.csv` עם כותרת, תיאור ו-13 תגיות לכל מודעה |
| `printify_sync.py` | יוצר את המוצרים ב-Printify ומפרסם אותם לחנות ה-Etsy המחוברת |
| `designs/` | כאן שמים את האיורים: `designs/<breed>.png` (PNG שקוף, 4500px לפחות) |

## הקמה (חד-פעמי, ידני)
1. פתיחת חנות Etsy וחשבון Printify, וחיבור ביניהם (Printify → My Stores → Etsy).
2. ב-Etsy: Shop Manager → Settings → Production partners → להוסיף את Printify.
3. ב-Printify: Settings → Orders → לסמן אישור ידני להזמנות, כדי להכניס את שם החיה מהשדה Personalization לפני ההדפסה.
4. ליצור טוקן API ב-Printify (My Account → Connections) ולשמור אותו כמשתנה סביבה `PRINTIFY_API_TOKEN`.

## הרצה
```bash
python catalog.py                                  # מייצר listings.csv
python printify_sync.py --shops                    # מציג את ה-shop_id
python printify_sync.py --find "ceramic ornament"  # בודק איזה מוצר נבחר בקטלוג
python printify_sync.py --shop <ID> --dry-run      # תצוגה מקדימה
python printify_sync.py --shop <ID> --only dachshund-ornament --publish   # בדיקה על מוצר אחד
python printify_sync.py --shop <ID> --publish      # כל השאר
```
הסקריפט שומר ב-`printify_state.json` מה כבר הועלה, כך שהרצה חוזרת לא יוצרת כפילויות.

**כדאי לבדוק ידנית את המוצר הראשון ב-Printify:** הספק שנבחר, מיקום ההדפסה והמחיר. רק אחרי זה מעלים את כל השאר.
