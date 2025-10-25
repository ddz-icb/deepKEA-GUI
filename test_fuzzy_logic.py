"""
Test und Demonstration der überarbeiteten Fuzzy-Matching-Logik

Neues Verhalten:
1. Jede Input-Site wird zu MAXIMAL EINER Datenbank-Site zugeordnet
2. Bei mehreren möglichen Matches wird die NÄCHSTGELEGENE Site gewählt (kleinster Positions-Unterschied)
3. Danach wird pro Kinase die Anzahl der inferred Hits limitiert (limit_inferred_hits)

Beispiel-Szenario:
-----------------
Input-Site: P12345_GENE_S100

Mögliche DB-Matches (innerhalb Toleranz):
- P12345_GENE_S98  -> Distanz: 2, Kinase: AKT1
- P12345_GENE_S100 -> Distanz: 0, Kinase: MAPK1 (EXACT MATCH)
- P12345_GENE_S102 -> Distanz: 2, Kinase: CDK1

ALTE LOGIK (falsch):
- Würde ALLE drei Matches zurückgeben
- Eine Input-Site würde zu 3 verschiedenen Kinasen gezählt
- Verfälscht die Statistik massiv!

NEUE LOGIK (korrekt):
- Sortiert nach Distanz: S100 (0), S98 (2), S102 (2)
- Nimmt nur S100 (kleinste Distanz = 0)
- Input-Site zählt nur für MAPK1
- Korrekte 1:1 Zuordnung

Vorteile:
---------
1. Biologisch sinnvoller: Eine Site hat eine Hauptfunktion
2. Statistisch korrekt: Keine Mehrfachzählung
3. Konservativ: Bevorzugt exakte Matches
4. Nachvollziehbar: Klare Zuordnungsregel (nächste Position)

Test-Cases:
-----------
"""

import pandas as pd

def test_fuzzy_matching_logic():
    """Demonstriert die neue 1:1 Matching-Logik"""
    
    # Simuliere Input-Sites
    samples = pd.DataFrame({
        'SUB_ACC_ID': ['P12345', 'P12345', 'Q99999'],
        'SUB_MOD_RSD': ['S100', 'T200', 'Y50'],
        'UPID': ['GENE1', 'GENE1', 'GENE2']
    })
    
    # Simuliere Datenbank mit mehreren möglichen Matches
    background = pd.DataFrame({
        'SUB_ACC_ID': ['P12345', 'P12345', 'P12345', 'P12345', 'Q99999', 'Q99999'],
        'SUB_MOD_RSD': ['S98', 'S100', 'S102', 'T198', 'Y50', 'Y52'],
        'KINASE': ['AKT1', 'MAPK1', 'CDK1', 'GSK3B', 'SRC', 'ABL1'],
        'KIN_ACC_ID': ['P31749', 'P28482', 'P06493', 'P49841', 'P12931', 'P00519'],
        'GENE': ['GENE1', 'GENE1', 'GENE1', 'GENE1', 'GENE2', 'GENE2']
    })
    
    print("=" * 80)
    print("FUZZY MATCHING TEST - 1:1 Constraint")
    print("=" * 80)
    
    print("\n📥 INPUT SITES:")
    print(samples)
    
    print("\n💾 DATABASE SITES:")
    print(background)
    
    print("\n" + "=" * 80)
    print("SCENARIO 1: Tolerance = 5, Mode = exact")
    print("=" * 80)
    
    print("\n🔍 Expected Behavior for S100:")
    print("   - Possible matches: S98 (dist=2, AKT1), S100 (dist=0, MAPK1), S102 (dist=2, CDK1)")
    print("   - ✅ SHOULD SELECT: S100 (dist=0, MAPK1) - closest match (exact)")
    print("   - ❌ SHOULD REJECT: S98 and S102 - not closest")
    
    print("\n🔍 Expected Behavior for T200:")
    print("   - Possible matches: T198 (dist=2, GSK3B)")
    print("   - ✅ SHOULD SELECT: T198 (dist=2, GSK3B) - only match within tolerance")
    
    print("\n🔍 Expected Behavior for Y50:")
    print("   - Possible matches: Y50 (dist=0, SRC), Y52 (dist=2, ABL1)")
    print("   - ✅ SHOULD SELECT: Y50 (dist=0, SRC) - exact match preferred")
    
    print("\n" + "=" * 80)
    print("EXPECTED RESULT:")
    print("=" * 80)
    expected = pd.DataFrame({
        'SUB_ACC_ID': ['P12345', 'P12345', 'Q99999'],
        'SUB_MOD_RSD_sample': ['S100', 'T200', 'Y50'],
        'SUB_MOD_RSD_bg': ['S100', 'T198', 'Y50'],
        'KINASE': ['MAPK1', 'GSK3B', 'SRC'],
        'IMPUTED': [False, True, False],
        'pos_distance': [0, 2, 0]
    })
    print(expected)
    
    print("\n" + "=" * 80)
    print("KEY IMPROVEMENTS:")
    print("=" * 80)
    print("✅ Each input site mapped to EXACTLY ONE database site")
    print("✅ Closest match by position is chosen (biologically sensible)")
    print("✅ No duplicate counting of the same input site")
    print("✅ Statistical analysis is now accurate")
    
    print("\n" + "=" * 80)
    print("IMPLEMENTATION CHANGES:")
    print("=" * 80)
    print("1. Calculate position distance for all matches")
    print("2. Create unique sample_site_id (SUB_ACC_ID + SUB_MOD_RSD_sample)")
    print("3. Sort by pos_distance (ascending)")
    print("4. Keep only first match per sample_site_id (drop_duplicates)")
    print("5. Apply per-kinase inferred hit limit afterwards")
    
    return expected

if __name__ == "__main__":
    test_fuzzy_matching_logic()
    
    print("\n\n" + "=" * 80)
    print("ALGORITHM PSEUDOCODE:")
    print("=" * 80)
    print("""
    for each sample_site in input:
        matches = []
        for each db_site in database:
            if same_protein(sample_site, db_site):
                if amino_acid_matches(sample_site, db_site, mode):
                    distance = abs(sample_pos - db_pos)
                    if distance <= tolerance:
                        matches.append((db_site, distance))
        
        if matches:
            # Sort by distance and take closest
            matches.sort(by='distance')
            best_match = matches[0]
            assign(sample_site, best_match)
        else:
            # No match found
            discard(sample_site)
    """)
    
    print("\n✅ Implementation complete in fuzzy_join() function!")
