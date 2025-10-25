# Fuzzy Matching Überarbeitung - Changelog

## Problem (Vorher)

Die alte Implementierung hatte ein **kritisches statistisches Problem**:

### Beispiel des Problems:
```
Input-Site: P12345_GENE_S100

Datenbank-Matches (innerhalb Toleranz=5):
- P12345_GENE_S98  -> Kinase: AKT1
- P12345_GENE_S100 -> Kinase: MAPK1
- P12345_GENE_S102 -> Kinase: CDK1
```

**Alte Logik:** Alle 3 Matches wurden akzeptiert
- ❌ Eine Input-Site wurde zu **3 verschiedenen Kinasen** gezählt
- ❌ Statistik massiv verfälscht (Mehrfachzählung)
- ❌ Eine Site zu S98, S100, UND S102 zugeordnet

**Resultat:** Künstlich aufgeblähte Hit-Counts für alle beteiligten Kinasen

---

## Lösung (Neu)

### Kernprinzip: **1:1 Zuordnung**
Jede Input-Site wird zu **maximal einer** Datenbank-Site zugeordnet.

### Auswahlkriterium: **Nächste Position**
Bei mehreren möglichen Matches wird die Site mit der **kleinsten Positions-Differenz** gewählt.

### Neue Logik im gleichen Beispiel:
```
Input-Site: P12345_GENE_S100

Mögliche Matches sortiert nach Distanz:
1. S100 (dist=0, MAPK1) ✅ GEWÄHLT
2. S98  (dist=2, AKT1)  ❌ VERWORFEN
3. S102 (dist=2, CDK1)  ❌ VERWORFEN
```

**Resultat:** 
- ✅ Input-Site zählt nur für MAPK1
- ✅ Keine Mehrfachzählung
- ✅ Statistisch korrekt

---

## Implementierung

### Änderungen in `fuzzy_join()`:

#### 1. Position-Distanz berechnen
```python
def match_and_calculate_distance(row):
    if aa_match(row['AA_sample'], row['AA_bg'], aa_mode):
        distance = abs(row['Pos_sample'] - row['Pos_bg'])
        if distance <= tolerance:
            is_imputed = distance > 0
            return True, is_imputed, distance  # ← Distanz hinzugefügt
    return False, None, None
```

#### 2. Eindeutige Sample-ID erstellen
```python
filtered['sample_site_id'] = filtered['SUB_ACC_ID'] + '_' + filtered['SUB_MOD_RSD_sample']
```

#### 3. Nach Distanz sortieren und deduplizieren
```python
# Sortiere nach Distanz (nächste zuerst)
filtered = filtered.sort_values('pos_distance')

# Behalte nur das erste (nächste) Match pro Input-Site
filtered_unique = filtered.drop_duplicates(subset=['sample_site_id'], keep='first')
```

### Verbesserungen in `limit_inferred_hits()`:

#### Klarere Logik:
```python
def keep_best_hits(group):
    # Exakte Matches (keine Imputation)
    exact = group[~group["IMPUTED"]].copy()
    
    # Inferred Matches (mit Imputation)
    inferred = group[group["IMPUTED"]].copy()
    
    # Behalte nur die nächsten N inferred hits
    if not inferred.empty and inferred_hit_limit > 0:
        inferred = inferred.sort_values("pos_diff", ascending=True).head(inferred_hit_limit)
    
    return pd.concat([exact, inferred], ignore_index=True)
```

---

## Vorteile

### 1. **Biologisch sinnvoll**
- Eine Phosphorylierungsstelle hat typischerweise eine Hauptfunktion
- Bevorzugung exakter Matches ist konservativ und korrekt

### 2. **Statistisch korrekt**
- Keine Mehrfachzählung der gleichen Input-Site
- Jede Site trägt genau 1× zur Statistik bei
- P-Werte sind jetzt aussagekräftig

### 3. **Nachvollziehbar**
- Klare Regel: "Nächste Position gewinnt"
- Deterministisch (gleicher Input → gleicher Output)
- Debugging ist einfacher

### 4. **Konservativ**
- Exakte Matches (Distanz = 0) werden immer bevorzugt
- Fuzzy Matches nur wenn nötig
- Reduziert False Positives

---

## Logging-Ausgaben

Die neue Implementation gibt hilfreiche Log-Meldungen aus:

```
Applying fuzzy matching with 1:1 constraint (closest match)...
Total matches before deduplication: 245
Matches after 1:1 deduplication (closest match per input site): 178
Removed 67 duplicate mappings
Before limiting: 178 total hits
After limiting: 156 total hits (max 7 inferred per kinase)
```

Dies zeigt:
1. Wie viele Mehrfach-Matches entfernt wurden
2. Wie viele Hits nach der Limitierung übrig bleiben
3. Transparenz über den gesamten Prozess

---

## Testen

Siehe `test_fuzzy_logic.py` für detaillierte Test-Szenarien und Beispiele.

---

## Zusammenfassung

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| **Zuordnung** | 1:n (eine Input-Site → viele DB-Sites) | 1:1 (eine Input-Site → eine DB-Site) |
| **Auswahlkriterium** | Alle innerhalb Toleranz | Nächste nach Position |
| **Mehrfachzählung** | ❌ Ja, Problem! | ✅ Nein, gelöst |
| **Statistik** | ❌ Verfälscht | ✅ Korrekt |
| **Nachvollziehbarkeit** | ❌ Schwierig | ✅ Klar definiert |

---

## Dateien geändert

1. **util.py**
   - `fuzzy_join()`: Neue 1:1 Logik implementiert
   - `limit_inferred_hits()`: Verbesserte Dokumentation und Logging

2. **test_fuzzy_logic.py** (NEU)
   - Test-Cases und Beispiele
   - Dokumentation der Logik

3. **FUZZY_MATCHING_CHANGES.md** (dieses Dokument)
   - Vollständige Dokumentation der Änderungen
