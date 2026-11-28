# scripts/diagnostic.py
"""
Diagnostic complet des performances Django.
Usage : python manage.py shell < scripts/diagnostic.py
"""

import os
from django.conf import settings
from django.db import connection
from django.db.models import Count
import time

print("=" * 70)
print("🔍 DIAGNOSTIC DJANGO — PERFORMANCES")
print("=" * 70)
print()

# ═══════════════════════════════════════════════════════════
# 1. CONFIGURATION CRITIQUE
# ═══════════════════════════════════════════════════════════
print("📋 1. CONFIGURATION")
print("-" * 70)

print(f"DEBUG              : {settings.DEBUG}")
if settings.DEBUG:
    print("   ⚠️  PROBLÈME : DEBUG=True ralentit Django de 2 à 10x")

print(f"Moteur DB          : {settings.DATABASES['default']['ENGINE']}")
print(f"Nom DB             : {settings.DATABASES['default']['NAME']}")
print(f"CONN_MAX_AGE       : {settings.DATABASES['default'].get('CONN_MAX_AGE', 'Non défini')}")
print(f"ALLOWED_HOSTS      : {settings.ALLOWED_HOSTS}")
print()

# ═══════════════════════════════════════════════════════════
# 2. VOLUMES DE DONNÉES
# ═══════════════════════════════════════════════════════════
print("📊 2. VOLUMES DE DONNÉES")
print("-" * 70)

from apps.users.models import User
from apps.dossiers.models import Dossier, EtapeCochee, DossierHistorique
from apps.dossiers.models import DossierAcces, IntituleDossier

tables = [
    ('User', User),
    ('Dossier', Dossier),
    ('EtapeCochee', EtapeCochee),
    ('DossierHistorique', DossierHistorique),
    ('DossierAcces', DossierAcces),
    ('IntituleDossier', IntituleDossier),
]

for name, model in tables:
    try:
        count = model.objects.count()
        print(f"{name:25} : {count:>10} lignes")
    except Exception as e:
        print(f"{name:25} : ERREUR ({e})")

print()

# ═══════════════════════════════════════════════════════════
# 3. TEST DE REQUÊTES SQL (le plus important)
# ═══════════════════════════════════════════════════════════
print("⚡ 3. TEST DE PERFORMANCE SQL")
print("-" * 70)

from django.test.utils import CaptureQueriesContext
from django.db import connection

# Test 1 : Liste simple des dossiers
with CaptureQueriesContext(connection) as ctx:
    start = time.time()
    dossiers = list(Dossier.objects.all()[:100])
    elapsed = (time.time() - start) * 1000

print(f"Test 1 : Dossier.objects.all()[:100]")
print(f"  → {len(dossiers)} lignes en {elapsed:.0f}ms")
print(f"  → {len(ctx.captured_queries)} requête(s) SQL")
if len(ctx.captured_queries) > 5:
    print(f"  ⚠️  NOMBREUSES REQUÊTES — probable N+1")

# Test 2 : Accès aux relations (le test N+1)
with CaptureQueriesContext(connection) as ctx:
    start = time.time()
    dossiers = list(Dossier.objects.all()[:50])
    for d in dossiers:
        _ = d.client.last_name if d.client else ''
        _ = d.intitule.name if d.intitule else ''
    elapsed = (time.time() - start) * 1000

print(f"\nTest 2 : Accès relations SANS select_related")
print(f"  → {len(dossiers)} lignes en {elapsed:.0f}ms")
print(f"  → {len(ctx.captured_queries)} requête(s) SQL")
if len(ctx.captured_queries) > 10:
    print(f"  🚨 PROBLÈME N+1 CONFIRMÉ ({len(ctx.captured_queries)} requêtes pour 50 lignes)")

# Test 3 : Même chose AVEC select_related
with CaptureQueriesContext(connection) as ctx:
    start = time.time()
    dossiers = list(Dossier.objects.select_related('client', 'intitule').all()[:50])
    for d in dossiers:
        _ = d.client.last_name if d.client else ''
        _ = d.intitule.name if d.intitule else ''
    elapsed = (time.time() - start) * 1000

print(f"\nTest 3 : Accès relations AVEC select_related")
print(f"  → {len(dossiers)} lignes en {elapsed:.0f}ms")
print(f"  → {len(ctx.captured_queries)} requête(s) SQL")
print(f"  ✅ Performance optimale")

# Test 4 : Compter les affectations par dossier
with CaptureQueriesContext(connection) as ctx:
    start = time.time()
    dossiers = list(Dossier.objects.all()[:100])
    for d in dossiers:
        _ = d.acces.count()
    elapsed = (time.time() - start) * 1000

print(f"\nTest 4 : d.acces.count() par dossier (N+1 classique)")
print(f"  → {len(dossiers)} lignes en {elapsed:.0f}ms")
print(f"  → {len(ctx.captured_queries)} requête(s) SQL")
if len(ctx.captured_queries) > 10:
    print(f"  🚨 N+1 sur les relations ManyToMany")

# Test 5 : Avec annotate (solution)
from django.db.models import Count

with CaptureQueriesContext(connection) as ctx:
    start = time.time()
    dossiers = list(
        Dossier.objects
        .select_related('client', 'intitule')
        .annotate(nb_acces=Count('acces'))
        .all()[:100]
    )
    elapsed = (time.time() - start) * 1000

print(f"\nTest 5 : Avec select_related + annotate")
print(f"  → {len(dossiers)} lignes en {elapsed:.0f}ms")
print(f"  → {len(ctx.captured_queries)} requête(s) SQL")
print(f"  ✅ Solution optimale")

print()

# ═══════════════════════════════════════════════════════════
# 4. INDEX EXISTANTS (SQLite)
# ═══════════════════════════════════════════════════════════
print("🗂️  4. INDEX SQLITE")
print("-" * 70)

with connection.cursor() as cursor:
    # Lister les index sur la table principale
    cursor.execute("""
        SELECT name, tbl_name, sql
        FROM sqlite_master
        WHERE type='index' AND tbl_name IN ('dossiers_dossier', 'users_user')
        ORDER BY tbl_name, name
    """)
    indexes = cursor.fetchall()
    
    if not indexes:
        print("  ⚠️  AUCUN INDEX détecté sur les tables principales")
    else:
        for name, table, sql in indexes:
            print(f"  • {table}.{name}")
            if sql:
                print(f"    {sql[:100]}...")

print()

# ═══════════════════════════════════════════════════════════
# 5. TAILLE DE LA BASE
# ═══════════════════════════════════════════════════════════
print("💾 5. TAILLE DE LA BASE")
print("-" * 70)

db_path = settings.DATABASES['default']['NAME']
if os.path.exists(db_path):
    size = os.path.getsize(db_path) / (1024 * 1024)
    print(f"Fichier : {db_path}")
    print(f"Taille  : {size:.2f} MB")
    if size > 100:
        print("  ⚠️  Base volumineuse — un VACUUM pourrait aider")
else:
    print(f"Fichier introuvable : {db_path}")

print()

# ═══════════════════════════════════════════════════════════
# 6. REQUÊTES LES PLUS LENTES (via EXPLAIN)
# ═══════════════════════════════════════════════════════════
print("🔎 6. ANALYSE DES REQUÊTES CRITIQUES")
print("-" * 70)

# Simuler les requêtes fréquentes avec EXPLAIN QUERY PLAN
requetes_test = [
    ("Liste clients", "SELECT * FROM users_user WHERE role = 'client' LIMIT 50"),
    ("Dossiers d'un client", "SELECT * FROM dossiers_dossier WHERE client_id = 1 LIMIT 50"),
    ("Dossiers récents", "SELECT * FROM dossiers_dossier ORDER BY created_at DESC LIMIT 50"),
    ("Dossiers par intitulé", "SELECT * FROM dossiers_dossier WHERE intitule_id = 1 LIMIT 50"),
    ("Étapes par dossier", "SELECT * FROM dossiers_etapecochee WHERE dossier_id = 1"),
]

with connection.cursor() as cursor:
    for label, query in requetes_test:
        try:
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plans = cursor.fetchall()
            print(f"\n{label} :")
            for plan in plans:
                detail = plan[-1] if isinstance(plan, tuple) else plan
                print(f"  {detail}")
                if 'SCAN' in str(detail).upper() and 'INDEX' not in str(detail).upper():
                    print("  ⚠️  SCAN COMPLET (pas d'index utilisé)")
        except Exception as e:
            print(f"\n{label} : Erreur ({e})")

print()

# ═══════════════════════════════════════════════════════════
# 7. RÉSUMÉ ET RECOMMANDATIONS
# ═══════════════════════════════════════════════════════════
print("=" * 70)
print("📝 RÉSUMÉ ET RECOMMANDATIONS")
print("=" * 70)

recommandations = []

if settings.DEBUG:
    recommandations.append("❌ Passer DEBUG=False en production")

if settings.DATABASES['default'].get('CONN_MAX_AGE', 0) == 0:
    recommandations.append("❌ Configurer CONN_MAX_AGE=600 (réutiliser les connexions)")

# Détection simple du N+1
with CaptureQueriesContext(connection) as ctx:
    dossiers = list(Dossier.objects.all()[:50])
    for d in dossiers:
        _ = d.client.last_name if d.client else ''
    nb_requetes = len(ctx.captured_queries)

if nb_requetes > 20:
    recommandations.append(f"❌ N+1 détecté : {nb_requetes} requêtes pour 50 lignes — utiliser select_related()")

if not recommandations:
    print("✅ Aucun problème critique détecté")
else:
    for r in recommandations:
        print(r)

print()
print("=" * 70)
print("FIN DU DIAGNOSTIC")
print("=" * 70)