"""
Optimized Course Name Translator
Features: Batch processing, caching, multithreading, progress bar
"""
import pandas as pd
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from tqdm import tqdm

try:
    from deep_translator import GoogleTranslator
    USE_TRANSLATOR = True
except ImportError:
    print("deep-translator not installed. Install with: pip install deep-translator")
    USE_TRANSLATOR = False

# Configuration
CACHE_FILE = "translation_cache.json"
MAX_WORKERS = 10  # Number of parallel threads
BATCH_SIZE = 100  # Save cache every N translations
RATE_LIMIT = 0.1  # Seconds between requests (faster with threading)

class TranslationCache:
    """Persistent cache for translations"""
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load()
        self.new_entries = 0

    def _load(self):
        """Load cache from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self, force=False):
        """Save cache to disk"""
        if self.new_entries > 0 or force:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            self.new_entries = 0

    def get(self, text):
        """Get cached translation"""
        return self.cache.get(text)

    def set(self, text, translation):
        """Store translation in cache"""
        self.cache[text] = translation
        self.new_entries += 1
        if self.new_entries >= BATCH_SIZE:
            self.save()

def is_english(text):
    """Check if text is already English/numeric"""
    if pd.isna(text):
        return True
    text = str(text).strip()
    if not text:
        return True
    # Check if mostly ASCII (allow some punctuation)
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / len(text) > 0.9

def translate_single(text, translator, cache, max_retries=3):
    """Translate a single text with caching and retry"""
    if not USE_TRANSLATOR:
        return text

    # Skip if already English
    if is_english(text):
        return text

    # Check cache
    cached = cache.get(text)
    if cached:
        return cached

    # Rate limiting (thread-safe via sleep)
    time.sleep(RATE_LIMIT)

    # Translate with exponential backoff
    for attempt in range(max_retries):
        try:
            result = translator.translate(str(text))
            cache.set(text, result)
            return result
        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                print(f"\nFailed: {text[:50]}... Error: {e}")
                cache.set(text, str(text))  # Cache original to avoid retry
                return str(text)

    return str(text)

def translate_batch(texts, translator, cache, progress_bar=None):
    """Translate a batch of texts using single thread"""
    results = []
    for text in texts:
        result = translate_single(text, translator, cache)
        results.append(result)
        if progress_bar:
            progress_bar.update(1)
    return results

def main():
    if not USE_TRANSLATOR:
        print("ERROR: deep-translator not installed")
        print("Run: pip install deep-translator tqdm")
        return

    # Initialize
    print("=" * 60)
    print("Optimized Course Concept Translator")
    print("=" * 60)

    translator = GoogleTranslator(source='zh-CN', target='en')
    cache = TranslationCache()

    # Check if input exists
    input_file = "C:\\Hanu\\year3\\year3_semester2\\BDM\\final_project\\MOOCCubeX\\data\\output\\course_concept_nottrans.csv\\part-00000-fff65bd5-5b83-4585-87d5-58f6881e127b-c000.csv"
    output_file = "C:\\Hanu\\year3\\year3_semester2\\BDM\\final_project\\MOOCCubeX\\data\\output\\course_concept_trans_en.csv"

    if not os.path.exists(input_file):
        print(f"\nERROR: {input_file} not found!")
        return

    # Read CSV
    print(f"\nReading {input_file}...")
    df = pd.read_csv(input_file)
    total = len(df)
    print(f"Total concepts: {total:,}")

    # Check already English
    english_count = sum(1 for concept in df['concept'] if is_english(concept))
    print(f"Already English: {english_count:,} ({english_count/total*100:.1f}%)")
    print(f"Need translation: {total - english_count:,}")

    # Statistics
    translated_count = 0

    print("\nTranslating with multithreading...")
    start_time = time.time()

    translations = [None] * total

    # Process in parallel with ThreadPool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_idx = {}
        for idx, concept in enumerate(df['concept']):
            if is_english(concept):
                translations[idx] = concept
            else:
                future = executor.submit(
                    translate_single, concept, translator, cache
                )
                future_to_idx[future] = idx

        # Progress bar
        with tqdm(total=len(future_to_idx), desc="Translating") as pbar:
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    translations[idx] = future.result()
                    translated_count += 1
                except Exception as e:
                    translations[idx] = str(df['name'].iloc[idx])
                    print(f"\nError at index {idx}: {e}")
                pbar.update(1)

    elapsed = time.time() - start_time

    # Final cache save
    cache.save(force=True)

    # Add to dataframe
    df['name_en'] = translations

    # Save output
    output_file = "name_course_trans_en.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')

    # Report
    print(f"\n{'='*60}")
    print("TRANSLATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total processed: {total:,}")
    print(f"Already English: {english_count:,}")
    print(f"Translated: {translated_count:,}")
    print(f"Cached: {len(cache.cache) - cache.new_entries:,}")
    print(f"Time: {elapsed:.1f}s ({total/elapsed:.1f} courses/sec)")
    print(f"\nOutput: {output_file}")

    # Sample
    print(f"\n{'='*60}")
    print("Sample translations:")
    print(f"{'='*60}")
    sample = df[df['name'] != df['name_en']].head(10)
    for _, row in sample.iterrows():
        print(f"  {row['name'][:50]:<50} -> {row['name_en'][:50]}")

if __name__ == "__main__":
    main()
