#!/usr/bin/env python3
"""
Intelligent Variant-Specification Mapper
Automatically maps variants to specifications using fuzzy matching and similarity scoring.
"""

import csv
import json
import os
import sys
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher


class VariantMapper:
    """
    A class to intelligently map variants to specifications using fuzzy matching.
    """
    
    def __init__(self, variant_file_path: str, specification_file_path: str, 
                 variants_mapping_json: str):
        """
        Initialize the VariantMapper with file paths.
        
        Args:
            variant_file_path: Path to the variant file (CSV/TXT/JSON)
            specification_file_path: Path to the specification file (CSV/TXT/JSON)
            variants_mapping_json: Path to the output variants mapping JSON file
        """
        self.variant_file_path = variant_file_path
        self.specification_file_path = specification_file_path
        self.variants_mapping_json = variants_mapping_json
        self.variants = []
        self.specifications = []
        self.mapping = {}
        self.confidence_scores = {}
        
        # Common abbreviations and their expansions
        self.abbreviations = {
            'OPT': ['(O)', 'PRO PACK', 'OPTIONAL'],
            'DT': ['DUAL TONE'],
            'DUAL CNG': ['CNG DUO', 'HY-CNG DUO', 'CNG'],
            'AMT': ['AMT'],
            'MT': ['MT'],
            'EXECUTIVE': ['EXECUTIVE'],
            'SMART': ['SMART'],
            'TECH': ['TECH'],
            'KNIGHT': ['KNIGHT EDITION'],
            'CONNECT': ['CONNECT'],
            'PLUS': ['PLUS'],
        }
    
    def load_csv_file(self, file_path: str) -> List[str]:
        """
        Load data from a CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of variant/specification names
        """
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if present
            header = next(reader, None)
            
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    data.append(row[0].strip())
        
        return data
    
    def load_txt_file(self, file_path: str) -> List[str]:
        """
        Load data from a TXT file.
        
        Args:
            file_path: Path to the TXT file
            
        Returns:
            List of variant/specification names
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    
    def load_json_file(self, file_path: str) -> List[str]:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of variant/specification names
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return list(data.keys())
            else:
                raise ValueError("JSON must be a list or dict")
    
    def load_file(self, file_path: str) -> List[str]:
        """
        Load data from a file (auto-detect format).
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of variant/specification names
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.endswith('.csv'):
            return self.load_csv_file(file_path)
        elif file_path.endswith('.json'):
            return self.load_json_file(file_path)
        else:
            return self.load_txt_file(file_path)
    
    def load_variants(self) -> List[str]:
        """Load the variant file."""
        self.variants = self.load_file(self.variant_file_path)
        return self.variants
    
    def load_specifications(self) -> List[str]:
        """Load the specification file."""
        self.specifications = self.load_file(self.specification_file_path)
        return self.specifications
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for better matching.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to uppercase
        text = text.upper().strip()
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text
    
    def tokenize(self, text: str) -> set:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            Set of tokens
        """
        normalized = self.normalize_text(text)
        return set(normalized.split())
    
    def calculate_similarity(self, variant: str, specification: str) -> float:
        """
        Calculate similarity score between variant and specification.
        
        Args:
            variant: Variant name
            specification: Specification name
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        variant_norm = self.normalize_text(variant)
        spec_norm = self.normalize_text(specification)
        
        # Base similarity using SequenceMatcher
        base_similarity = SequenceMatcher(None, variant_norm, spec_norm).ratio()
        
        # Token-based matching
        variant_tokens = self.tokenize(variant)
        spec_tokens = self.tokenize(specification)
        
        # Calculate token overlap
        if variant_tokens:
            token_overlap = len(variant_tokens & spec_tokens) / len(variant_tokens)
        else:
            token_overlap = 0.0
        
        # Check for abbreviation matches
        abbrev_bonus = 0.0
        for abbrev, expansions in self.abbreviations.items():
            if abbrev in variant_norm:
                for expansion in expansions:
                    if expansion in spec_norm:
                        abbrev_bonus += 0.15
                        break
        
        # Handle special cases
        special_bonus = 0.0
        
        # AMT matching
        if 'AMT' in variant_norm and 'AMT' in spec_norm:
            special_bonus += 0.1
        elif 'AMT' in variant_norm and 'MT' in spec_norm and 'AMT' not in spec_norm:
            special_bonus -= 0.3  # Penalty for mismatch
        
        # MT matching (when AMT is not present)
        if 'AMT' not in variant_norm and 'MT' in spec_norm:
            special_bonus += 0.05
        
        # CNG matching
        if 'CNG' in variant_norm or 'DUAL CNG' in variant_norm:
            if 'CNG' in spec_norm or 'CNG DUO' in spec_norm or 'HY-CNG' in spec_norm:
                special_bonus += 0.15
        
        # DUAL TONE / DT matching
        if 'DT' in variant_norm or 'DUAL TONE' in variant_norm:
            if 'DUAL TONE' in spec_norm:
                special_bonus += 0.15
        
        # KNIGHT matching
        if 'KNIGHT' in variant_norm and 'KNIGHT' in spec_norm:
            special_bonus += 0.1
        
        # OPT matching with (O) or PRO PACK
        if 'OPT' in variant_norm:
            if '(O)' in spec_norm or 'PRO PACK' in spec_norm:
                special_bonus += 0.15
        
        # CONNECT matching
        if 'CONNECT' in variant_norm and 'CONNECT' in spec_norm:
            special_bonus += 0.1
        
        # Base model matching (first token must match)
        variant_first = variant_norm.split()[0] if variant_norm.split() else ""
        spec_first = spec_norm.split()[0] if spec_norm.split() else ""
        
        if variant_first and spec_first and variant_first == spec_first:
            special_bonus += 0.1
        
        # Combine scores with weights
        final_score = (
            base_similarity * 0.3 +
            token_overlap * 0.4 +
            abbrev_bonus +
            special_bonus
        )
        
        # Cap at 1.0
        return min(final_score, 1.0)
    
    def find_best_match(self, variant: str) -> Tuple[Optional[str], float]:
        """
        Find the best matching specification for a variant.
        
        Args:
            variant: Variant name
            
        Returns:
            Tuple of (best_match, confidence_score)
        """
        if not self.specifications:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for spec in self.specifications:
            score = self.calculate_similarity(variant, spec)
            
            if score > best_score:
                best_score = score
                best_match = spec
        
        return best_match, best_score
    
    def create_mapping(self, confidence_threshold: float = 0.5) -> Dict[str, str]:
        """
        Create automatic mapping between variants and specifications.
        
        Args:
            confidence_threshold: Minimum confidence score for mapping (0.0 to 1.0)
            
        Returns:
            Dictionary mapping variants to specifications
        """
        if not self.variants:
            self.load_variants()
        
        if not self.specifications:
            self.load_specifications()
        
        used_specifications = set()
        
        # Sort variants to process longer/more specific ones first
        sorted_variants = sorted(self.variants, key=lambda x: len(x), reverse=True)
        
        for variant in sorted_variants:
            # Find best match among unused specifications
            available_specs = [s for s in self.specifications if s not in used_specifications]
            
            if not available_specs:
                # All specs used, allow reuse for remaining variants
                available_specs = self.specifications
            
            best_match = None
            best_score = 0.0
            
            for spec in available_specs:
                score = self.calculate_similarity(variant, spec)
                if score > best_score:
                    best_score = score
                    best_match = spec
            
            if best_match and best_score >= confidence_threshold:
                self.mapping[variant] = best_match
                self.confidence_scores[variant] = best_score
                used_specifications.add(best_match)
            else:
                self.mapping[variant] = None
                self.confidence_scores[variant] = best_score
        
        return self.mapping
    
    def save_mapping(self, include_confidence: bool = True) -> None:
        """
        Save the mapping to a JSON file.
        
        Args:
            include_confidence: Whether to include confidence scores in output
        """
        output = {}
        
        for variant, spec in self.mapping.items():
            if include_confidence:
                output[variant] = {
                    "specification": spec,
                    "confidence": round(self.confidence_scores.get(variant, 0.0), 3)
                }
            else:
                output[variant] = spec
        
        with open(self.variants_mapping_json, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Mapping saved to: {self.variants_mapping_json}")
    
    def display_mapping(self, show_confidence: bool = True) -> None:
        """
        Display the mapping in a readable format.
        
        Args:
            show_confidence: Whether to show confidence scores
        """
        print("\n" + "=" * 100)
        print("VARIANT TO SPECIFICATION MAPPING")
        print("=" * 100)
        
        # Calculate statistics
        total = len(self.mapping)
        mapped = sum(1 for v in self.mapping.values() if v is not None)
        unmapped = total - mapped
        
        # Separate into mapped and unmapped
        mapped_variants = {k: v for k, v in self.mapping.items() if v is not None}
        unmapped_variants = {k: v for k, v in self.mapping.items() if v is None}
        
        # Display mapped variants
        if mapped_variants:
            print(f"\n✓ SUCCESSFULLY MAPPED ({mapped}):\n")
            for variant, spec in sorted(mapped_variants.items()):
                confidence = self.confidence_scores.get(variant, 0.0)
                confidence_indicator = "●" if confidence >= 0.8 else "◐" if confidence >= 0.6 else "○"
                
                if show_confidence:
                    print(f"  {confidence_indicator} {variant:35} → {spec:50} [{confidence:.2f}]")
                else:
                    print(f"  {confidence_indicator} {variant:35} → {spec}")
        
        # Display unmapped variants
        if unmapped_variants:
            print(f"\n✗ UNMAPPED ({unmapped}):\n")
            for variant in sorted(unmapped_variants.keys()):
                confidence = self.confidence_scores.get(variant, 0.0)
                print(f"  ✗ {variant:35} (best score: {confidence:.2f})")
        
        print("\n" + "=" * 100)
        print(f"SUMMARY: {mapped}/{total} mapped ({(mapped/total*100):.1f}%), {unmapped} unmapped")
        print("=" * 100 + "\n")
        
        # Show unmapped specifications
        mapped_specs = set(v for v in self.mapping.values() if v is not None)
        unmapped_specs = [s for s in self.specifications if s not in mapped_specs]
        
        if unmapped_specs:
            print(f"\n⚠ UNUSED SPECIFICATIONS ({len(unmapped_specs)}):\n")
            for spec in sorted(unmapped_specs):
                print(f"  • {spec}")
            print()
    
    def display_statistics(self) -> None:
        """Display detailed statistics about the mapping."""
        print("\n" + "=" * 100)
        print("MAPPING STATISTICS")
        print("=" * 100)
        
        if self.confidence_scores:
            scores = [s for s in self.confidence_scores.values() if s > 0]
            
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                
                high_conf = sum(1 for s in scores if s >= 0.8)
                med_conf = sum(1 for s in scores if 0.6 <= s < 0.8)
                low_conf = sum(1 for s in scores if 0.5 <= s < 0.6)
                very_low = sum(1 for s in scores if s < 0.5)
                
                print(f"Average Confidence: {avg_score:.3f}")
                print(f"Highest Confidence: {max_score:.3f}")
                print(f"Lowest Confidence:  {min_score:.3f}")
                print(f"\nConfidence Distribution:")
                print(f"  High (≥0.8):      {high_conf} mappings")
                print(f"  Medium (0.6-0.8): {med_conf} mappings")
                print(f"  Low (0.5-0.6):    {low_conf} mappings")
                print(f"  Very Low (<0.5):  {very_low} mappings")
        
        print("=" * 100 + "\n")


def main():
    """Main function to run the variant mapper."""
    
    # Default file paths
    variant_file_path = "variants.csv"
    specification_file_path = "specifications.csv"
    variants_mapping_json = "variants_mapping.json"
    
    # Check if custom paths are provided via command line
    if len(sys.argv) >= 4:
        variant_file_path = sys.argv[1]
        specification_file_path = sys.argv[2]
        variants_mapping_json = sys.argv[3]
    
    # Optional confidence threshold
    confidence_threshold = 0.5
    if len(sys.argv) >= 5:
        try:
            confidence_threshold = float(sys.argv[4])
        except ValueError:
            print(f"Warning: Invalid confidence threshold, using default: {confidence_threshold}")
    
    print("=" * 100)
    print("INTELLIGENT VARIANT-SPECIFICATION MAPPER")
    print("=" * 100)
    print(f"\nVariant File:        {variant_file_path}")
    print(f"Specification File:  {specification_file_path}")
    print(f"Output JSON:         {variants_mapping_json}")
    print(f"Confidence Threshold: {confidence_threshold}")
    print()
    
    try:
        # Initialize the mapper
        mapper = VariantMapper(
            variant_file_path=variant_file_path,
            specification_file_path=specification_file_path,
            variants_mapping_json=variants_mapping_json
        )
        
        # Load files
        print("📂 Loading variants...")
        variants = mapper.load_variants()
        print(f"   Loaded {len(variants)} variants")
        
        print("📂 Loading specifications...")
        specs = mapper.load_specifications()
        print(f"   Loaded {len(specs)} specifications")
        
        # Create mapping
        print("\n🔍 Analyzing and creating mappings...")
        mapper.create_mapping(confidence_threshold=confidence_threshold)
        
        # Display results
        mapper.display_mapping(show_confidence=True)
        mapper.display_statistics()
        
        # Save mapping
        mapper.save_mapping(include_confidence=True)
        
        print("✓ Process completed successfully!\n")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()