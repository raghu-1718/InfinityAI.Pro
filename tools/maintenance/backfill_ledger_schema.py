# Backfill Ledger Schema Maintenance Tool
# InfinityAI.Pro - Normalizes legacy Firestore ai_signals_ledger documents

import argparse
import logging
from google.cloud import firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BackfillLedgerSchema')

def backfill_schema(project_id: str = 'project-841b7f97-5ee3-4fbe-920', execute: bool = False):
    db = firestore.Client(project=project_id)
    col_ref = db.collection('ai_signals_ledger')
    docs = list(col_ref.stream())
    logger.info(f'Fetched {len(docs)} total documents from ai_signals_ledger')

    updated_count = 0
    for doc in docs:
        data = doc.to_dict()
        doc_id = doc.id
        updates = {}

        # 1. Backfill settlement_type if missing and trade is resolved
        if not data.get('settlement_type'):
            status = data.get('outcome_status', 'OPEN')
            if 'TARGET' in status:
                updates['settlement_type'] = 'TARGET_REACHED'
            elif 'STOP' in status or 'LOSS' in status:
                updates['settlement_type'] = 'STOP_LOSS_REACHED'
            elif 'EOD' in status:
                updates['settlement_type'] = 'EOD_AUTO_SQUAREOFF'
            elif status == 'RESOLVED':
                updates['settlement_type'] = 'HISTORICAL_RESOLVED'

        # 2. Backfill highest_observed_premium if missing
        if data.get('highest_observed_premium') is None:
            exit_prem = data.get('exit_premium')
            entry_prem = (data.get('trade_bracket') or {}).get('entry_premium', 100.0)
            updates['highest_observed_premium'] = exit_prem if exit_prem is not None else entry_prem

        if updates:
            updated_count += 1
            if execute:
                col_ref.document(doc_id).update(updates)
                logger.info(f'✅ [COMMITTED] {doc_id} -> {updates}')
            else:
                logger.info(f'🔍 [DRY-RUN] Would update {doc_id} with: {updates}')

    mode = 'COMMITTED' if execute else 'DRY-RUN (Pass --execute to commit)'
    logger.info(f'Completed. {updated_count} documents identified for schema normalization. [{mode}]')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backfill Firestore Ledger Schema')
    parser.add_argument('--execute', action='store_true', help='Commit changes to Firestore')
    args = parser.parse_args()
    backfill_schema(execute=args.execute)
