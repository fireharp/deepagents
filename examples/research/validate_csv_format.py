#!/usr/bin/env python3
"""
Validate WooCommerce CSV format by attempting to parse and analyze the generated files.
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import re


def validate_csv_structure(csv_path: str, expected_type: str) -> Dict[str, Any]:
    """Validate CSV structure and format."""
    validation_result = {
        'file': csv_path,
        'type': expected_type,
        'valid': True,
        'errors': [],
        'warnings': [],
        'stats': {},
        'sample_rows': []
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Check if file uses semicolon delimiter
            sample = f.read(1024)
            f.seek(0)
            
            if ';' not in sample:
                validation_result['errors'].append("CSV should use semicolon (;) as delimiter")
                validation_result['valid'] = False
            
            # Parse CSV with proper delimiter
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            
            validation_result['stats']['total_rows'] = len(rows)
            validation_result['stats']['columns'] = len(reader.fieldnames) if reader.fieldnames else 0
            validation_result['stats']['fieldnames'] = reader.fieldnames
            
            # Store first few rows for inspection
            validation_result['sample_rows'] = rows[:3]
            
            if not rows:
                validation_result['errors'].append("CSV file is empty")
                validation_result['valid'] = False
                return validation_result
            
            # Validate required columns based on type
            required_es_columns = [
                'sku', 'post_title', 'post_content', 'post_excerpt', 
                'regular_price', 'stock_status',
                'attribute:pa_pais', 'attribute:pa_region', 'attribute:pa_tipo',
                'attribute:pa_uva', 'attribute:pa_uva-principal',
                'attribute:pa_enologo-bodega', 'attribute:pa_como-servirlo',
                'attribute:pa_graduacion-alcoholica'
            ]
            
            required_en_columns = ['wpml:original_product_sku'] + required_es_columns
            
            expected_columns = required_en_columns if expected_type == 'EN' else required_es_columns
            
            missing_columns = [col for col in expected_columns if col not in reader.fieldnames]
            if missing_columns:
                validation_result['errors'].append(f"Missing required columns: {missing_columns}")
                validation_result['valid'] = False
            
            # Validate data quality
            for i, row in enumerate(rows):
                row_errors = []
                
                # Check required fields are not empty
                critical_fields = ['sku', 'post_title', 'regular_price', 'stock_status']
                for field in critical_fields:
                    if not row.get(field, '').strip():
                        row_errors.append(f"Row {i+1}: Empty {field}")
                
                # Validate price format
                price = row.get('regular_price', '')
                if price and not re.match(r'^\d+\.\d{2}$', price):
                    row_errors.append(f"Row {i+1}: Invalid price format '{price}' (should be XX.XX)")
                
                # Validate stock status
                stock = row.get('stock_status', '')
                if stock and stock not in ['instock', 'outofstock']:
                    row_errors.append(f"Row {i+1}: Invalid stock_status '{stock}'")
                
                # Check for pipe separators in multi-value fields
                multi_value_fields = ['attribute:pa_uva', 'attribute:pa_uva-principal']
                for field in multi_value_fields:
                    value = row.get(field, '')
                    if value and '|' in value:
                        # Check for spaces around pipes (should not have)
                        if ' |' in value or '| ' in value:
                            row_errors.append(f"Row {i+1}: {field} has spaces around pipes")
                
                # EN-specific validations
                if expected_type == 'EN':
                    original_sku = row.get('wpml:original_product_sku', '')
                    if not original_sku:
                        row_errors.append(f"Row {i+1}: Missing wpml:original_product_sku")
                
                if row_errors:
                    validation_result['warnings'].extend(row_errors[:5])  # Limit warnings
                    if len(row_errors) > 5:
                        validation_result['warnings'].append(f"Row {i+1}: ... and {len(row_errors)-5} more issues")
                
    except Exception as e:
        validation_result['errors'].append(f"Failed to parse CSV: {str(e)}")
        validation_result['valid'] = False
    
    return validation_result


def validate_bilingual_consistency(es_csv: str, en_csv: str) -> Dict[str, Any]:
    """Validate consistency between ES and EN CSV files."""
    consistency_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    try:
        # Read both files
        with open(es_csv, 'r', encoding='utf-8') as f:
            es_reader = csv.DictReader(f, delimiter=';')
            es_rows = list(es_reader)
        
        with open(en_csv, 'r', encoding='utf-8') as f:
            en_reader = csv.DictReader(f, delimiter=';')
            en_rows = list(en_reader)
        
        # Check row counts match
        if len(es_rows) != len(en_rows):
            consistency_result['errors'].append(f"Row count mismatch: ES={len(es_rows)}, EN={len(en_rows)}")
            consistency_result['valid'] = False
        
        consistency_result['stats']['es_rows'] = len(es_rows)
        consistency_result['stats']['en_rows'] = len(en_rows)
        
        # Check WPML linking
        es_skus = {row['sku'] for row in es_rows}
        en_original_skus = {row.get('wpml:original_product_sku', '') for row in en_rows}
        
        # Check if all EN rows link to existing ES rows
        unlinked_skus = en_original_skus - es_skus
        if unlinked_skus:
            consistency_result['errors'].append(f"EN rows link to non-existent ES SKUs: {unlinked_skus}")
            consistency_result['valid'] = False
        
        # Check for missing links
        missing_links = es_skus - en_original_skus
        if missing_links:
            consistency_result['warnings'].append(f"ES SKUs without EN counterpart: {missing_links}")
        
        # Check attribute translations
        translation_fields = ['attribute:pa_pais', 'attribute:pa_tipo', 'attribute:pa_uva-principal']
        translation_issues = []
        
        for es_row, en_row in zip(es_rows, en_rows):
            for field in translation_fields:
                es_value = es_row.get(field, '')
                en_value = en_row.get(field, '')
                
                # Check if values are different (indicating translation)
                if es_value and en_value and es_value == en_value:
                    # Same value might indicate missing translation
                    if field == 'attribute:pa_pais' and es_value in ['España', 'Francia', 'Italia']:
                        translation_issues.append(f"Possible untranslated {field}: {es_value}")
                    elif field == 'attribute:pa_tipo' and es_value in ['Tinto', 'Blanco', 'Rosado']:
                        translation_issues.append(f"Possible untranslated {field}: {es_value}")
        
        if translation_issues:
            # Only show unique issues
            unique_issues = list(set(translation_issues))[:10]  # Limit to 10
            consistency_result['warnings'].extend(unique_issues)
        
    except Exception as e:
        consistency_result['errors'].append(f"Failed to validate consistency: {str(e)}")
        consistency_result['valid'] = False
    
    return consistency_result


def test_csv_import_simulation(csv_path: str) -> Dict[str, Any]:
    """Simulate importing the CSV as if it were being imported into WooCommerce."""
    import_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'processed_products': 0,
        'sample_product': {}
    }
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            for i, row in enumerate(reader):
                # Simulate basic import validation
                sku = row.get('sku', '').strip()
                if not sku:
                    import_result['errors'].append(f"Product {i+1}: Missing SKU")
                    continue
                
                title = row.get('post_title', '').strip()
                if not title:
                    import_result['errors'].append(f"Product {sku}: Missing title")
                
                price = row.get('regular_price', '').strip()
                try:
                    if price:
                        float(price)
                except ValueError:
                    import_result['errors'].append(f"Product {sku}: Invalid price '{price}'")
                
                # Store first product as sample
                if i == 0:
                    import_result['sample_product'] = {
                        'sku': sku,
                        'title': title,
                        'price': price,
                        'country': row.get('attribute:pa_pais', ''),
                        'type': row.get('attribute:pa_tipo', ''),
                        'grapes': row.get('attribute:pa_uva-principal', ''),
                        'producer': row.get('attribute:pa_enologo-bodega', ''),
                    }
                
                import_result['processed_products'] += 1
        
        if import_result['errors']:
            import_result['valid'] = False
    
    except Exception as e:
        import_result['errors'].append(f"Import simulation failed: {str(e)}")
        import_result['valid'] = False
    
    return import_result


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate WooCommerce CSV format")
    parser.add_argument('--csv-dir', default='csv_exports_all', help='Directory containing CSV files')
    
    args = parser.parse_args()
    
    csv_dir = args.csv_dir
    es_csv = os.path.join(csv_dir, 'products_es.csv')
    en_csv = os.path.join(csv_dir, 'products_en.csv')
    
    print("🔍 Validating WooCommerce CSV Format\n")
    
    # Check if files exist
    if not os.path.exists(es_csv):
        print(f"❌ ES CSV not found: {es_csv}")
        return
    
    if not os.path.exists(en_csv):
        print(f"❌ EN CSV not found: {en_csv}")
        return
    
    # Validate ES CSV
    print("📄 Validating Spanish CSV...")
    es_result = validate_csv_structure(es_csv, 'ES')
    
    if es_result['valid']:
        print(f"✅ ES CSV structure is valid")
        print(f"   📊 {es_result['stats']['total_rows']} products, {es_result['stats']['columns']} columns")
    else:
        print(f"❌ ES CSV has issues:")
        for error in es_result['errors']:
            print(f"   - {error}")
    
    if es_result['warnings']:
        print(f"⚠️  ES CSV warnings:")
        for warning in es_result['warnings'][:10]:  # Limit warnings
            print(f"   - {warning}")
    
    # Validate EN CSV
    print("\n📄 Validating English CSV...")
    en_result = validate_csv_structure(en_csv, 'EN')
    
    if en_result['valid']:
        print(f"✅ EN CSV structure is valid")
        print(f"   📊 {en_result['stats']['total_rows']} products, {en_result['stats']['columns']} columns")
    else:
        print(f"❌ EN CSV has issues:")
        for error in en_result['errors']:
            print(f"   - {error}")
    
    if en_result['warnings']:
        print(f"⚠️  EN CSV warnings:")
        for warning in en_result['warnings'][:10]:  # Limit warnings
            print(f"   - {warning}")
    
    # Validate bilingual consistency
    print("\n🔗 Validating bilingual consistency...")
    consistency_result = validate_bilingual_consistency(es_csv, en_csv)
    
    if consistency_result['valid']:
        print("✅ Bilingual consistency is valid")
        print(f"   📊 ES: {consistency_result['stats']['es_rows']} rows, EN: {consistency_result['stats']['en_rows']} rows")
    else:
        print("❌ Bilingual consistency issues:")
        for error in consistency_result['errors']:
            print(f"   - {error}")
    
    if consistency_result['warnings']:
        print("⚠️  Bilingual warnings:")
        for warning in consistency_result['warnings'][:5]:  # Limit warnings
            print(f"   - {warning}")
    
    # Test import simulation
    print("\n🔄 Simulating WooCommerce import...")
    es_import = test_csv_import_simulation(es_csv)
    en_import = test_csv_import_simulation(en_csv)
    
    if es_import['valid'] and en_import['valid']:
        print("✅ Import simulation successful")
        print(f"   📦 ES: {es_import['processed_products']} products")
        print(f"   📦 EN: {en_import['processed_products']} products")
        
        # Show sample product
        if es_import['sample_product']:
            sample = es_import['sample_product']
            print(f"\n📋 Sample product (ES):")
            print(f"   SKU: {sample['sku']}")
            print(f"   Title: {sample['title'][:50]}...")
            print(f"   Price: {sample['price']}")
            print(f"   Country: {sample['country']}")
            print(f"   Type: {sample['type']}")
            print(f"   Producer: {sample['producer'][:30]}...")
    else:
        print("❌ Import simulation failed")
        if not es_import['valid']:
            print("   ES import errors:")
            for error in es_import['errors'][:5]:
                print(f"   - {error}")
        if not en_import['valid']:
            print("   EN import errors:")
            for error in en_import['errors'][:5]:
                print(f"   - {error}")
    
    # Overall summary
    all_valid = es_result['valid'] and en_result['valid'] and consistency_result['valid'] and es_import['valid'] and en_import['valid']
    
    print(f"\n{'='*60}")
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED! CSV files are ready for WooCommerce import.")
    else:
        print("⚠️  Some validations failed. Please review the issues above.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
