import { useState, useEffect } from 'react';
import { ShieldAlert, ShieldCheck, Activity } from 'lucide-react';

interface Transaction {
  transaction_id: string;
  user_id: string;
  amount: number;
  status: string;
  fraud_score: number;
}

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Connect to the FastAPI WebSocket we just created
    const socket = new WebSocket('ws://127.0.0.1:8000/ws/transactions');

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);

    socket.onmessage = (event) => {
      const newTxn: Transaction = JSON.parse(event.data);
      // We add the newest transaction to the top of the list
      setTransactions((prev) => [newTxn, ...prev].slice(0, 50)); // Keep only latest 50
    };

    return () => socket.close();
  }, []);

  return (
    <div className="min-h-screen p-8">
      {/* Header Section */}
      <header className="flex justify-between items-center mb-8 border-b border-slate-700 pb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Activity className="text-blue-500" /> Sentinel AI Dashboard
          </h1>
          <p className="text-slate-400 mt-2">Real-time Fraud Monitoring System</p>
        </div>
        <div className="flex gap-4">
          <div className={`px-4 py-2 rounded-full flex items-center gap-2 text-sm font-medium ${connected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
            {connected ? 'System Live' : 'System Offline'}
          </div>
        </div>
      </header>

      {/* Main Feed */}
      <div className="grid grid-cols-1 gap-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-slate-900/50 text-slate-400 text-sm uppercase">
              <tr>
                <th className="px-6 py-4">ID</th>
                <th className="px-6 py-4">User</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">AI Verdict</th>
                <th className="px-6 py-4 text-right">Fraud Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {transactions.map((txn) => (
                <tr key={txn.transaction_id} className={`transition-colors ${txn.status === 'flagged' ? 'bg-red-500/10' : 'hover:bg-slate-700/50'}`}>
                  <td className="px-6 py-4 font-mono text-xs text-slate-400">{txn.transaction_id.slice(0, 8)}...</td>
                  <td className="px-6 py-4 text-sm">{txn.user_id}</td>
                  <td className="px-6 py-4 font-semibold">${txn.amount.toFixed(2)}</td>
                  <td className="px-6 py-4">
                    <span className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold w-fit uppercase ${txn.status === 'flagged' ? 'bg-red-500 text-white animate-pulse' : 'bg-green-500/20 text-green-400'}`}>
                      {txn.status === 'flagged' ? <ShieldAlert size={14} /> : <ShieldCheck size={14} />}
                      {txn.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right font-mono">
                    <span className={txn.fraud_score > 0.5 ? 'text-red-400' : 'text-slate-400'}>
                      {(txn.fraud_score * 100).toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500 italic">
                    Waiting for incoming transaction data...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;