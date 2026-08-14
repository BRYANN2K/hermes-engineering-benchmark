export function buildTableModel(rows, options = {}) {
  return { rows, total: rows.length, page: 1, pageSize: 10, totalPages: 1, summary: '', empty: null };
}
