# simulate_time.py
import os
import sys
import django
from datetime import timedelta, datetime
from django.utils import timezone

# Configuration Django - CORRIGÉ
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dossiers.models import Dossier, EtapeGlobale, EtapeCochee, DossierHistorique

def simulate_advancement(dossier_pk, days=30, verbose=True):
    """
    Simule l'avancement du temps de 'days' jours pour un dossier.
    
    Args:
        dossier_pk: ID du dossier à tester
        days: Nombre de jours à avancer (30 par défaut = 1 mois)
        verbose: Afficher les détails
    """
    
    # Récupérer le dossier
    try:
        dossier = Dossier.objects.get(pk=dossier_pk)
    except Dossier.DoesNotExist:
        print(f"❌ Dossier {dossier_pk} introuvable")
        return
    
    print("=" * 80)
    print(f"🚀 SIMULATION D'AVANCEMENT DU TEMPS - {days} JOURS")
    print("=" * 80)
    print(f"📋 Dossier: {dossier.reference} - {dossier.get_title()}")
    print(f"📅 Date actuelle: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📅 Date simulée: {(timezone.now() + timedelta(days=days)).strftime('%d/%m/%Y %H:%M')}")
    print("-" * 80)
    
    # État initial
    print("\n📊 ÉTAT INITIAL:")
    print(f"  Technique: {dossier.get_progression_technique()}% / {dossier.get_total_technique()}%")
    print(f"  Morcellement: {dossier.get_progression_morcellement()}% / {dossier.get_total_morcellement()}%")
    print(f"  Statut: {dossier.get_statut_display()}")
    
    # Récupérer toutes les étapes cochées
    cochees = dossier.etapes_cochees.select_related('etape').all()
    
    print("\n📋 ÉTAPES AVANT SIMULATION:")
    for c in cochees.order_by('etape__type', 'etape__order'):
        status = "✅" if c.is_done else "⬜"
        auto = f"auto: {c.date_auto_coche.strftime('%d/%m/%Y')}" if c.date_auto_coche else "MANUELLE"
        done_by = f"par {c.done_by}" if c.done_by else "auto"
        print(f"  {status} {c.etape.name} ({c.etape.get_type_display()}) - {auto} - {done_by}")
    
    print("\n" + "-" * 80)
    print("⏳ AVANCEMENT DU TEMPS...")
    print("-" * 80)
    
    # 🔥 SIMULATION - Avancer le temps
    # Pour simuler, on va modifier les dates de coché automatique
    # pour qu'elles soient dans le passé
    
    modified_count = 0
    for cochee in cochees.filter(date_auto_coche__isnull=False, is_done=False):
        # Modifier la date pour simuler le passage du temps
        nouvelle_date = cochee.date_auto_coche - timedelta(days=days)
        if verbose:
            print(f"🔄 Simulation: {cochee.etape.name} - Date modifiée de {cochee.date_auto_coche.strftime('%d/%m/%Y')} à {nouvelle_date.strftime('%d/%m/%Y')}")
        cochee.date_auto_coche = nouvelle_date
        cochee.save()
        modified_count += 1
    
    if modified_count == 0:
        print("ℹ️ Aucune étape à simuler (toutes sont déjà cochées ou manuelles)")
    
    print("\n" + "-" * 80)
    print("🔄 APPLICATION DES COCHES AUTOMATIQUES...")
    print("-" * 80)
    
    # Appliquer les coches automatiques
    try:
        dossier.appliquer_cochages_automatiques()
        dossier.refresh_from_db()
        print("✅ Coché automatique appliqué avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de l'application: {e}")
        import traceback
        traceback.print_exc()
    
    # 🔄 Recharger les données
    dossier.refresh_from_db()
    cochees = dossier.etapes_cochees.select_related('etape').all()
    
    print("\n📊 ÉTAT FINAL:")
    print(f"  Technique: {dossier.get_progression_technique()}% / {dossier.get_total_technique()}%")
    print(f"  Morcellement: {dossier.get_progression_morcellement()}% / {dossier.get_total_morcellement()}%")
    print(f"  Statut: {dossier.get_statut_display()}")
    
    print("\n📋 ÉTAPES APRÈS SIMULATION:")
    for c in cochees.order_by('etape__type', 'etape__order'):
        status = "✅" if c.is_done else "⬜"
        auto = f"auto: {c.date_auto_coche.strftime('%d/%m/%Y')}" if c.date_auto_coche else "MANUELLE"
        done_by = f"par {c.done_by}" if c.done_by else "auto"
        print(f"  {status} {c.etape.name} ({c.etape.get_type_display()}) - {auto} - {done_by}")
    
    # Vérifier les règles
    print("\n🔍 VÉRIFICATION DES RÈGLES:")
    
    # 1. Dernière étape technique = manuelle
    etapes_tech = list(EtapeGlobale.objects.filter(type='technique').order_by('order'))
    if etapes_tech:
        last_tech = etapes_tech[-1]
        cochee_last = cochees.filter(etape=last_tech).first()
        if cochee_last:
            if cochee_last.done_by is not None or not cochee_last.is_done:
                print(f"  ✅ Dernière étape technique '{last_tech.name}' est manuelle")
            else:
                print(f"  ❌ Dernière étape technique '{last_tech.name}' est automatique ! Problème !")
        else:
            print(f"  ⚠️ Dernière étape technique '{last_tech.name}' n'existe pas")
    
    # 2. Première étape morcellement = manuelle
    etapes_morc = list(EtapeGlobale.objects.filter(type='morcellement').order_by('order'))
    if etapes_morc:
        first_morc = etapes_morc[0]
        cochee_first = cochees.filter(etape=first_morc).first()
        if cochee_first:
            if cochee_first.done_by is not None or not cochee_first.is_done:
                print(f"  ✅ Première étape morcellement '{first_morc.name}' est manuelle")
            else:
                print(f"  ❌ Première étape morcellement '{first_morc.name}' est automatique ! Problème !")
        else:
            print(f"  ⚠️ Première étape morcellement '{first_morc.name}' n'existe pas")
    
    # 3. Dernière étape morcellement = manuelle
    if len(etapes_morc) > 1:
        last_morc = etapes_morc[-1]
        cochee_last = cochees.filter(etape=last_morc).first()
        if cochee_last:
            if cochee_last.done_by is not None or not cochee_last.is_done:
                print(f"  ✅ Dernière étape morcellement '{last_morc.name}' est manuelle")
            else:
                print(f"  ❌ Dernière étape morcellement '{last_morc.name}' est automatique ! Problème !")
        else:
            print(f"  ⚠️ Dernière étape morcellement '{last_morc.name}' n'existe pas")
    
    # 4. Vérifier le blocage du morcellement
    if not dossier.is_technique_complete():
        # Vérifier qu'aucune étape morcellement n'est cochée
        morc_cochees = cochees.filter(etape__type='morcellement', is_done=True)
        if morc_cochees.exists():
            print(f"  ❌ Technique pas complète mais des étapes morcellement sont cochées ! Problème !")
            for c in morc_cochees:
                print(f"     - {c.etape.name} est cochée")
        else:
            print(f"  ✅ Aucune étape morcellement cochée (technique pas complète)")
    else:
        print(f"  ✅ Technique complète, le morcellement peut avancer")
    
    # 5. Vérification des historiques
    historiques = dossier.historique.all().order_by('-created_at')[:10]
    if historiques.exists():
        print(f"\n📝 DERNIERS ÉVÉNEMENTS DE L'HISTORIQUE:")
        for h in historiques:
            print(f"  [{h.created_at.strftime('%d/%m/%Y %H:%M')}] {h.message}")
    
    print("\n" + "=" * 80)
    print("✅ SIMULATION TERMINÉE")
    
    return dossier

def verification_complete(dossier_pk):
    """
    Vérification complète du système
    """
    print("\n" + "=" * 80)
    print("🔍 VÉRIFICATION COMPLÈTE DU SYSTÈME")
    print("=" * 80)
    
    dossier = Dossier.objects.get(pk=dossier_pk)
    
    # 1. Vérifier que les dates sont bien planifiées
    cochees_sans_date = dossier.etapes_cochees.filter(
        date_auto_coche__isnull=True,
        is_done=False
    ).select_related('etape')
    
    print("\n📋 ÉTAPES SANS DATE AUTO (manuelles):")
    for c in cochees_sans_date:
        print(f"  - {c.etape.name} ({c.etape.get_type_display()})")
        if c.etape.type == 'technique':
            etapes_tech = list(EtapeGlobale.objects.filter(type='technique').order_by('order'))
            if etapes_tech and c.etape.pk == etapes_tech[-1].pk:
                print(f"    ✅ Dernière étape technique - OK")
            else:
                print(f"    ⚠️ Cette étape devrait être automatique")
        elif c.etape.type == 'morcellement':
            etapes_morc = list(EtapeGlobale.objects.filter(type='morcellement').order_by('order'))
            if etapes_morc and c.etape.pk == etapes_morc[0].pk:
                print(f"    ✅ Première étape morcellement - OK")
            elif etapes_morc and c.etape.pk == etapes_morc[-1].pk:
                print(f"    ✅ Dernière étape morcellement - OK")
            else:
                print(f"    ⚠️ Cette étape devrait être automatique")
    
    # 2. Vérifier les dates planifiées
    cochees_avec_date = dossier.etapes_cochees.filter(
        date_auto_coche__isnull=False
    ).select_related('etape')
    
    print("\n📅 ÉTAPES AVEC DATE AUTO:")
    for c in cochees_avec_date:
        status = "✅ OK" if c.is_done else "⏳ En attente"
        print(f"  - {c.etape.name} ({c.etape.get_type_display()}) - {c.date_auto_coche.strftime('%d/%m/%Y')} - {status}")
    
    # 3. Vérifier le respect des règles
    print("\n📊 STATUT DU DOSSIER:")
    print(f"  Technique: {dossier.get_progression_technique()}%")
    print(f"  Morcellement: {dossier.get_progression_morcellement()}%")
    print(f"  Technique complète: {'✅ OUI' if dossier.is_technique_complete() else '❌ NON'}")
    print(f"  Morcellement complète: {'✅ OUI' if dossier.is_morcellement_complete() else '❌ NON'}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Simuler l\'avancement du temps')
    parser.add_argument('dossier_pk', type=int, help='ID du dossier')
    parser.add_argument('--days', type=int, default=30, help='Nombre de jours à simuler (défaut: 30)')
    parser.add_argument('--verbose', action='store_true', help='Afficher plus de détails')
    
    args = parser.parse_args()
    
    # Lancer la simulation
    simulate_advancement(args.dossier_pk, args.days, args.verbose)
    
    # Vérification complète
    if args.verbose:
        verification_complete(args.dossier_pk)