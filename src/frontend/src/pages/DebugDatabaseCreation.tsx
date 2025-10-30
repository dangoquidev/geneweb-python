import { useState } from 'react'

export default function DebugDatabaseCreation() {
  const [dbName, setDbName] = useState('test_debug_component')
  const [status, setStatus] = useState('')
  const [response, setResponse] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const testApiConnection = async () => {
    setStatus('🔍 Test de connexion API...')
    setResponse(null)

    try {
      const url = 'http://127.0.0.1:8000/api/databases'
      console.log('Testing connection to:', url)

      const res = await fetch(url)
      const data = await res.json()

      setStatus(`✅ API accessible (${res.status})`)
      setResponse(data)
      console.log('API Response:', data)
    } catch (error: any) {
      setStatus(`❌ Erreur de connexion: ${error.message}`)
      console.error('Connection error:', error)
    }
  }

  const createDatabase = async () => {
    setLoading(true)
    setStatus('📝 Création de la base...')
    setResponse(null)

    try {
      const url = 'http://127.0.0.1:8000/api/databases'
      const payload = {
        name: dbName,
        db_type: 'pickle'
      }

      console.log('POST to:', url)
      console.log('Payload:', payload)

      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      console.log('Response status:', res.status)
      console.log('Response headers:', Object.fromEntries(res.headers.entries()))

      const data = await res.json()
      console.log('Response data:', data)

      if (res.ok) {
        setStatus(`✅ Base créée avec succès! (${res.status})`)
        setResponse(data)
      } else {
        setStatus(`❌ Erreur ${res.status}: ${data.detail || data.message || 'Erreur inconnue'}`)
        setResponse(data)
      }
    } catch (error: any) {
      setStatus(`❌ Exception: ${error.message}`)
      setResponse({ error: error.message, stack: error.stack })
      console.error('Creation error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>🔬 Debug: Création de Base de Données</h1>

      <div style={{ marginTop: '20px', padding: '10px', background: '#f0f0f0', borderRadius: '5px' }}>
        <h3>Configuration</h3>
        <p><strong>API URL:</strong> http://127.0.0.1:8000/api</p>
        <p><strong>VITE_API_URL:</strong> {import.meta.env.VITE_API_URL || 'undefined'}</p>
      </div>

      <div style={{ marginTop: '20px' }}>
        <button
          onClick={testApiConnection}
          style={{
            padding: '10px 20px',
            marginRight: '10px',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Test Connexion API
        </button>
      </div>

      <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}>
        <h3>Créer une base</h3>
        <div>
          <label>
            Nom de la base:
            <input
              type="text"
              value={dbName}
              onChange={(e) => setDbName(e.target.value)}
              style={{
                marginLeft: '10px',
                padding: '5px',
                width: '300px'
              }}
            />
          </label>
        </div>
        <button
          onClick={createDatabase}
          disabled={loading || !dbName}
          style={{
            marginTop: '10px',
            padding: '10px 20px',
            background: loading ? '#999' : '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Création...' : 'Créer la Base'}
        </button>
      </div>

      {status && (
        <div style={{
          marginTop: '20px',
          padding: '10px',
          background: status.includes('✅') ? '#d4edda' : status.includes('❌') ? '#f8d7da' : '#d1ecf1',
          borderRadius: '5px'
        }}>
          <strong>Status:</strong> {status}
        </div>
      )}

      {response && (
        <div style={{ marginTop: '20px' }}>
          <h3>Réponse de l'API:</h3>
          <pre style={{
            padding: '10px',
            background: '#f5f5f5',
            borderRadius: '5px',
            overflow: 'auto'
          }}>
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}

      <div style={{ marginTop: '20px', padding: '10px', background: '#fff3cd', borderRadius: '5px' }}>
        <h3>📋 Instructions</h3>
        <ol>
          <li>Ouvrir la console développeur (F12)</li>
          <li>Cliquer sur "Test Connexion API"</li>
          <li>Vérifier les logs dans la console</li>
          <li>Essayer de créer une base</li>
          <li>Noter les erreurs exactes</li>
        </ol>
      </div>
    </div>
  )
}
