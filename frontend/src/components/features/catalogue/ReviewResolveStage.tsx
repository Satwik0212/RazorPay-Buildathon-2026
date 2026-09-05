import React, { useEffect, useState } from "react";
import { Loader2, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw, XCircle } from "lucide-react";
import { Button } from "../../ui/Button";
import { catalogueImportApi } from "../../../api/catalogueImport";
import type { AnalyzedRow } from "../../../api/catalogueImport";

interface Props {
  importJobId: string;
  onResolvedAll: () => void;
  onCancel: () => void;
}

export const ReviewResolveStage: React.FC<Props> = ({ importJobId, onResolvedAll, onCancel }) => {
  const [rows, setRows] = useState<AnalyzedRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [resolving, setResolving] = useState<number | null>(null);

  const fetchRows = async () => {
    try {
      const res = await catalogueImportApi.getReviewRows(importJobId);
      setRows(res.data.rows);
      if (res.data.rows.length === 0) {
        onResolvedAll();
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to fetch rows for review.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRows();
  }, [importJobId]);

  const handleAction = async (rowIndex: number, action: 'ACCEPT' | 'EDIT' | 'EXCLUDE', updatedFields?: any) => {
    setResolving(rowIndex);
    setError("");
    try {
      const res = await catalogueImportApi.resolveRow(importJobId, rowIndex, action, updatedFields);
      // Remove or update the row locally
      if (res.data.row.status === 'READY' || res.data.row.status === 'EXCLUDED') {
        const newRows = rows.filter(r => r.row_index !== rowIndex);
        setRows(newRows);
        if (newRows.length === 0) onResolvedAll();
      } else {
        setRows(rows.map(r => r.row_index === rowIndex ? res.data.row : r));
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || `Failed to ${action.toLowerCase()} row.`);
    } finally {
      setResolving(null);
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center py-12"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>;
  }

  if (rows.length === 0) {
    return (
      <div className="text-center py-8">
        <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
        <h3 className="font-semibold text-lg text-gray-800">All Issues Resolved</h3>
        <p className="text-gray-500 text-sm mb-4">You have successfully reviewed and resolved all data issues.</p>
        <Button onClick={onResolvedAll}>Continue to Preview</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="font-semibold text-amber-800 text-sm">Action Required</h4>
          <p className="text-xs text-amber-700 mt-1">
            {rows.length} rows have missing fields, validations errors, or warnings. You must resolve these before confirming the import.
          </p>
        </div>
      </div>
      
      {error && <div className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>}

      <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
        {rows.map(row => (
          <RowCard 
            key={row.row_index} 
            row={row} 
            resolving={resolving === row.row_index} 
            onResolve={(action, updates) => handleAction(row.row_index, action, updates)} 
          />
        ))}
      </div>

      <div className="flex gap-2 pt-2">
        <Button variant="outline" onClick={onCancel} className="flex-1">â†  Back to Mapping</Button>
      </div>
    </div>
  );
};

const RowCard = ({ row, resolving, onResolve }: { row: AnalyzedRow, resolving: boolean, onResolve: (action: 'ACCEPT'|'EDIT'|'EXCLUDE', fields?: any) => void }) => {
  const isFix = row.status === 'NEEDS_FIX';
  const isDup = row.status === 'DUPLICATE';
  
  // Minimal edit state
  const [editing, setEditing] = useState(false);
  const [editValues, setEditValues] = useState<any>({});

  const handleEditChange = (field: string, val: string) => {
    setEditValues({ ...editValues, [field]: val });
  };

  const saveEdit = () => {
    const formatted: any = {};
    for (const [k, v] of Object.entries(editValues)) {
      if (k === 'price' || k === 'retail_price' || k === 'discounted_price') {
        formatted[k] = parseInt(v as string, 10);
      } else {
        formatted[k] = v;
      }
    }
    onResolve('EDIT', formatted);
    setEditing(false);
  };

  return (
    <div className={`border rounded-lg p-3 ${isFix || isDup ? 'border-red-200 bg-red-50/30' : 'border-yellow-200 bg-yellow-50/30'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isFix || isDup ? <XCircle className="w-4 h-4 text-red-500" /> : <AlertCircle className="w-4 h-4 text-yellow-500" />}
          <span className="font-semibold text-sm text-gray-800">
            Row {row.row_index}: {row.normalized_candidate.product_name || 'Unnamed Product'}
          </span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${isFix || isDup ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>
            {row.status}
          </span>
        </div>
      </div>
      
      <div className="text-xs space-y-1 mb-3">
        {row.issues.map((iss, idx) => (
          <div key={idx} className="text-gray-600">
            <span className="font-medium text-gray-800">{iss.field}:</span> {iss.error} 
            {iss.original_value !== undefined && <span className="text-gray-400 ml-1">(original: {iss.original_value})</span>}
          </div>
        ))}
      </div>

      {editing ? (
        <div className="bg-white p-2 rounded border space-y-2 mb-3">
          <p className="text-xs font-semibold text-gray-700 mb-1">Edit Canonical Fields:</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {['product_name', 'category', 'retail_price', 'discounted_price'].map(f => (
              <div key={f}>
                <label className="block text-gray-500 mb-0.5">{f}</label>
                <input 
                  type={f.includes('price') ? 'number' : 'text'} 
                  className="w-full border rounded px-2 py-1"
                  defaultValue={row.normalized_candidate[f] || ''}
                  onChange={(e) => handleEditChange(f, e.target.value)}
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2 justify-end mt-2">
            <Button variant="outline" size="sm" onClick={() => setEditing(false)}>Cancel</Button>
            <Button size="sm" onClick={saveEdit} disabled={resolving}>Save & Validate</Button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => onResolve('EXCLUDE')} disabled={resolving}>
            Exclude
          </Button>
          <Button variant="outline" size="sm" onClick={() => setEditing(true)} disabled={resolving}>
            Edit
          </Button>
          {!isFix && !isDup && (
            <Button size="sm" onClick={() => onResolve('ACCEPT')} disabled={resolving} className="ml-auto bg-green-600 hover:bg-green-700">
              {resolving ? <Loader2 className="w-3 h-3 animate-spin" /> : "Accept Warning"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
