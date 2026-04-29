import pandas as pd
import time

try:
    from deep_translator import GoogleTranslator
    USE_TRANSLATOR = True
    translator = GoogleTranslator(source='zh-CN', target='en')
except ImportError:
    print("deep-translator not installed. Install with: pip install deep-translator")
    USE_TRANSLATOR = False

def translate_text(text, max_retries=3):
    """Translate Chinese text to English with retry logic"""
    if not USE_TRANSLATOR:
        return f"[INSTALL deep-translator: pip install deep-translator] {text}"

    # Skip if already English or numeric
    if all(ord(c) < 128 for c in str(text)):
        return str(text)

    for attempt in range(max_retries):
        try:
            time.sleep(0.2)  # Rate limiting
            result = translator.translate(str(text))
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed: {text[:30]}... Error: {e}")
                return str(text)
            time.sleep(1)
    return str(text)

def main():
    print("Reading CSV...")
    df = pd.read_csv("name_course_not_trans.csv")
    total = len(df)
    print(f"Total courses: {total}")

    print("\nTranslating...")
    translations = []

    for idx, name in enumerate(df['name']):
        translated = translate_text(name)
        translations.append(translated)

        if (idx + 1) % 100 == 0:
            print(f"  {idx + 1}/{total} done ({(idx+1)/total*100:.1f}%)")

    df['name_en'] = translations

    # Save
    df.to_csv("name_course_trans_en.csv", index=False)
    print(f"\n✓ Saved to: name_course_trans_en.csv")

    # Show sample
    print("\nSample:")
    for i in range(min(10, len(df))):
        print(f"  {df['name'].iloc[i]} -> {df['name_en'].iloc[i]}")

if __name__ == "__main__":
    main()
