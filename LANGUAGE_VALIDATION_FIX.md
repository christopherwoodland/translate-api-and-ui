# Language Validation Fix

## Issue Identified

The translation system was **not validating** whether the source language and target language are the same before submitting translation jobs to Azure. This could result in:

1. **Wasted API calls** - Translating a document from English to English
2. **Unnecessary costs** - Azure charges for each translation, even if no actual translation occurs
3. **User confusion** - Users might think translation failed when it actually "succeeded" with no changes

## Root Cause

None of the translation scripts (`single_document_translation.py`, `batch_translation.py`, `ocr_translation_pipeline.py`) included validation to check if:
- The specified source language matches the target language
- When auto-detecting, if the detected language matches the target

## Changes Made

### 1. Single Document Translation (`single_document_translation.py`)
- **Added validation**: When `source_language` is specified, compare it to `target_language` before creating translation job
- **Raises ValueError**: If languages match, prevents API call and returns clear error message
- **Added warning**: When auto-detecting, warns user that we cannot validate until after translation completes

```python
# Before translation job submission
if source_language:
    if source_language.lower() == target_language.lower():
        error_msg = f"Source language ({source_language}) and target language ({target_language}) are the same - no translation needed"
        logger.error(error_msg)
        raise ValueError(error_msg)
```

### 2. Batch Translation (`batch_translation.py`)
- **Added validation**: Checks if specified `source_language` matches ANY of the target languages
- **Raises ValueError**: If match found, prevents batch translation job
- **Lists all matching languages**: Error message shows which target languages match the source

```python
if source_language:
    matching_langs = [lang for lang in target_languages if lang.lower() == source_language.lower()]
    if matching_langs:
        error_msg = f"Source language ({source_language}) matches target language(s): {', '.join(matching_langs)} - no translation needed"
        logger.error(error_msg)
        raise ValueError(error_msg)
```

### 3. OCR Translation Pipeline (`ocr_translation_pipeline.py`)
- **Added validation**: Same as single document translation
- **Raises ValueError**: Before submitting OCR'd document for translation

```python
if source_language and source_language.lower() == target_language.lower():
    error_msg = f"Source language ({source_language}) and target language ({target_language}) are the same - no translation needed"
    print(f"Error: {error_msg}")
    raise ValueError(error_msg)
```

## Limitation: Auto-Detection

**Important**: When using auto-detection (no `source_language` specified), the validation **cannot prevent** same-language translations because:

1. Azure Document Translation API does **not** return the detected source language in the response
2. The API detects language internally but doesn't expose it
3. We only know the source language was "auto-detected" after the translation completes

### Why This Happens

According to Azure documentation:
- The Document Translation API auto-detects source language internally
- The response includes `status` and URLs but **not** the detected language code
- This is different from the Text Translation API which does return detected language

### Workaround for Users

To ensure source and target languages are different:
1. **Specify source language explicitly** when you know it (recommended)
2. Use the Text Translation API first to detect language if needed
3. Review translated documents to verify actual translation occurred

## Testing

To test the fix:

### Test 1: Explicit Source Language (Should Fail)
```python
translator = SingleDocumentTranslator()
translator.translate_document(
    input_file_path="document.pdf",
    target_language="en",
    source_language="en"  # Same as target
)
# Expected: ValueError raised before API call
```

### Test 2: Batch with Matching Language (Should Fail)
```python
translator = BatchDocumentTranslator()
translator.translate_batch(
    input_folder="docs/",
    target_languages=["en", "fr", "es"],
    source_language="en"  # Matches "en" in targets
)
# Expected: ValueError raised, lists "en" as matching language
```

### Test 3: Auto-Detection (Will Warn)
```python
translator = SingleDocumentTranslator()
translator.translate_document(
    input_file_path="document.pdf",
    target_language="en"
    # No source_language specified
)
# Expected: Proceeds with translation, logs warning about inability to validate
```

## Error Messages

Users will now see clear error messages:

**Single/OCR Translation:**
```
Error: Source language (en) and target language (en) are the same - no translation needed
```

**Batch Translation:**
```
Error: Source language (en) matches target language(s): en - no translation needed
```

**Auto-Detection Warning (in logs):**
```
WARNING: Source language was auto-detected - cannot verify if it matches target (en)
If the document is already in en, the translation may be unnecessary
```

## Recommendations

1. **Update Web UI**: Add JavaScript validation to prevent selecting same source/target in the UI
2. **Add language detection endpoint**: Use Azure Text Translation API's `/detect` endpoint to detect language before translation
3. **Cost tracking**: Monitor translation costs to identify patterns of same-language translations
4. **User education**: Update documentation to recommend specifying source language when known

## Files Modified

- `single_document_translation.py` - Lines ~275-285 (validation) + Lines ~318-325 (warning)
- `batch_translation.py` - Lines ~276-282 (validation)
- `ocr_translation_pipeline.py` - Lines ~335-340 (validation)

## Impact

- ✅ Prevents wasted API calls when source language is known
- ✅ Saves translation costs
- ✅ Provides clear error messages to users
- ⚠️ Cannot prevent auto-detected same-language translations (Azure API limitation)
- ✅ Warns users when auto-detection is used

---

**Date**: October 23, 2025  
**Issue Reported**: User noticed source and target languages might be the same  
**Resolution**: Added validation for all translation types with explicit source language
