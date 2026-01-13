import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'
import motivationImg from './assets/motivation.jpg'
import { Globe, Box, Terminal, Eraser, Search, Loader2, Wallet, ArrowRightLeft, Video, MessageCircle, FileText, Download, Activity, Image as ImageIcon, X } from 'lucide-react'
import { ethers } from 'ethers'

function App() {
  const [activeModule, setActiveModule] = useState('console')
  const [discordStatus, setDiscordStatus] = useState({ connected: false, active: false, lastActivity: null })
  const [consoleInput, setConsoleInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentActivity, setCurrentActivity] = useState(null)
  const [evelineSessions, setEvelineSessions] = useState([])
  const [notes, setNotes] = useState([])
  const [notesCategory, setNotesCategory] = useState(null)
  const consoleOutputRef = useRef(null)
  const abortControllerRef = useRef(null) // New AbortController Ref
  const [consoleHistory, setConsoleHistory] = useState(() => {
    const saved = localStorage.getItem('terminal_os_history')
    return saved ? JSON.parse(saved) : [
      { type: 'system', text: 'TERMINAL_OS v1.1.0 - Powered by Mistral AI' },
      { type: 'system', text: 'Backend connected on 127.0.0.1:8000' },
      { type: 'system', text: 'EVELINE_WARMUP: System context loaded.' },
      { type: 'system', text: 'AI Ready - Everything is optimized.' }
    ]
  })
  const [sessionId, setSessionId] = useState(() => {
    let sid = localStorage.getItem('terminal_os_session_id')
    if (!sid) {
      sid = crypto.randomUUID()
      localStorage.setItem('terminal_os_session_id', sid)
    }
    return sid
  })
  const [pendingImage, setPendingImage] = useState(null) // Server response after upload (legacy/fallback)
  const [pendingFile, setPendingFile] = useState(null)   // RAW file waiting to be sent
  const [previewUrl, setPreviewUrl] = useState(null)     // Local preview URL
  const fileInputRef = useRef(null)

  // Persistence Effect
  useEffect(() => {
    localStorage.setItem('terminal_os_history', JSON.stringify(consoleHistory))
    scrollToBottom()
  }, [consoleHistory])

  const scrollToBottom = () => {
    if (consoleOutputRef.current) {
      consoleOutputRef.current.scrollTop = consoleOutputRef.current.scrollHeight
    }
  }

  const fetchNotes = async () => {
    try {
      const response = await fetch('/api/notes')
      if (response.ok) {
        const data = await response.json()
        setNotes(data)
      }
    } catch (err) {
      console.error('Failed to fetch notes:', err)
    }
  }

  const [selectedNote, setSelectedNote] = useState(null)

  const downloadSingleNote = (note) => {
    const element = document.createElement("a");
    const file = new Blob([note.content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${note.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.txt`;
    document.body.appendChild(element); // Required for this to work in FireFox
    element.click();
    document.body.removeChild(element);
  }

  useEffect(() => {
    if (activeModule === 'notes') {
      fetchNotes()
    }
  }, [activeModule])

  // STOP FUNCTION
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      addToHistory('system', '🛑 SYSTEM INTERRUPT: Task stopped by user.');
      setIsLoading(false);
      setCurrentActivity(null);
    }
  };

  const renderTextWithLinks = (text) => {
    if (typeof text !== 'string') return text;
    const parts = text.split(/(\[[^\]]+\]\([^\)]+\))/g);
    return parts.map((part, i) => {
      const match = part.match(/\[([^\]]+)\]\(([^\)]+)\)/);
      if (match) {
        return (
          <a
            key={i}
            href={match[2]}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--accent-blue)', textDecoration: 'underline', cursor: 'pointer' }}
          >
            {match[1]}
          </a>
        );
      }
      return part;
    });
  };

  const renderGroup = (group) => (
    <div key={group.key} className="agent-activity-group">
      <div className="group-header">
        <Loader2 size={12} className="spin" />
        <span>AGENT_ACTIVITY_LOG</span>
      </div>
      <div className="group-steps">
        {group.steps.map((step, sIdx) => {
          // Détection spéciale pour les images
          let imageData = null;
          try {
            if (step.output && (typeof step.output === 'string' && (step.output.startsWith('{') || step.output.startsWith('[')))) {
              const parsed = JSON.parse(step.output);
              // Handle both "image_results" (old) and direct array (Node.js service style)
              if (parsed.type === "image_results" && parsed.images) {
                imageData = parsed; // Old format
              } else if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].image_url) {
                imageData = { images: parsed, query: step.input }; // New Node.js format adaptation
              }
            }
          } catch (e) {
            // Pas du JSON valide ou pas le bon format, on ignore
          }

          // Détection spéciale pour les vidéos
          let videoData = null;
          try {
            if (step.output && (typeof step.output === 'string' && (step.output.startsWith('{') || step.output.startsWith('[')))) {
              const parsed = JSON.parse(step.output);
              if (Array.isArray(parsed) && parsed.length > 0 && (parsed[0].url || parsed[0].video_url)) {
                videoData = { videos: parsed, query: step.input };
              }
            }
          } catch (e) { }

          // Détection spéciale pour OSINT
          let osintData = null;
          try {
            if (step.output && (typeof step.output === 'string' && (step.output.startsWith('{') || step.output.startsWith('[')))) {
              const parsed = JSON.parse(step.output);
              if (parsed.status === "SUCCESS" && parsed.domain) {
                osintData = { type: "domain", data: parsed, target: step.input };
              } else if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].platform) {
                osintData = { type: "username", data: parsed, target: step.input };
              }
            }
          } catch (e) { }

          if (osintData) {
            return (
              <div key={sIdx} className="step-item osint-results">
                <div className="step-main">
                  <Search size={12} />
                  <span className="step-label">[FOOTPRINT_REPORT]</span>
                  <span className="step-input">{osintData.target}</span>
                </div>
                {osintData.type === "username" ? (
                  <div className="osint-grid">
                    {osintData.data.map((res, idx) => (
                      <div key={idx} className="osint-card" onClick={() => window.open(res.url, '_blank')} style={{ cursor: 'pointer' }}>
                        <span className="platform">{res.platform}</span>
                        <span className="url">{res.url}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="osint-domain-info">
                    <div className="osint-report-header">DOMAIN_ANALYSIS: {osintData.data.domain}</div>
                    <div><span className="osint-label">Registrar:</span> <span className="osint-value">{osintData.data.registrar}</span></div>
                    <div><span className="osint-label">Created:</span> <span className="osint-value">{osintData.data.creation_date}</span></div>
                    <div><span className="osint-label">Expires:</span> <span className="osint-value">{osintData.data.expiration_date}</span></div>
                    <div><span className="osint-label">IP Addresses:</span> <span className="osint-value">{osintData.data.ips.join(', ')}</span></div>
                  </div>
                )}
              </div>
            );
          }

          if (videoData) {
            return (
              <div key={sIdx} className="step-item video-results">
                <div className="step-main">
                  <Video size={12} />
                  <span className="step-label">[VIDEO_RECOMMENDATIONS]</span>
                  <span className="step-input">{videoData.query}</span>
                </div>
                <div className="video-grid">
                  {videoData.videos.map((vid, idx) => (
                    <div key={idx} className="video-card" onClick={() => window.open(vid.url || vid.video_url, '_blank')}>
                      <div className="video-thumb-container">
                        <img src={vid.thumbnail_url} alt={vid.title} loading="lazy" />
                        {vid.duration && <span className="video-duration">{vid.duration}</span>}
                      </div>
                      <div className="video-info">
                        <div className="video-title" title={vid.title}>{vid.title}</div>
                        <div className="video-meta">
                          <span className="platform-badge">{vid.platform || 'YouTube'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          if (imageData) {
            return (
              <div key={sIdx} className="step-item image-results">
                <div className="step-main">
                  <Globe size={12} />
                  <span className="step-label">[IMAGE_SEARCH]</span>
                  <span className="step-input">{imageData.query}</span>
                </div>
                <div className="image-grid">
                  {imageData.images.slice(0, 6).map((img, idx) => (
                    <div key={idx} className="image-item">
                      <img
                        src={img.thumbnail_url || img.image_url}
                        alt={img.title}
                        loading="lazy"
                        onClick={() => window.open(img.source_url, '_blank')}
                      />
                      <div className="image-caption">{img.title}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          // Private Tool Detection
          let isPrivate = false;
          try {
            if (step.input) {
              // Check if input reflects a private action (either JSON flag or implicit convention)
              const inputStr = String(step.input);
              if (inputStr.includes('"private": true') || inputStr.includes('"private":true')) isPrivate = true;
              // Also check specific tool output for privacy flags if needed
            }
          } catch (e) { }

          if (isPrivate) {
            return (
              <div key={sIdx} className="step-item private-step" style={{ opacity: 0.5, fontSize: '0.8em', padding: '5px' }}>
                <div className="step-main">
                  <span className="step-icon"><Loader2 size={10} /></span>
                  <span className="step-label">[INTERNAL_PROCESS]</span>
                  <span className="step-status">➔ COMPLETED</span>
                </div>
              </div>
            )
          }

          return (
            <div key={sIdx} className={`step-item ${step.tool.toLowerCase()}`}>
              <div className="step-main">
                <span className="step-icon">
                  {step.tool === 'SCRAPE' && <Globe size={12} />}
                  {step.tool === 'SEARCH' && <Search size={12} />}
                  {step.tool === 'SANDBOX' && <Box size={12} />}
                  {step.tool === 'COMMAND' && <Terminal size={12} />}
                  {step.tool === 'MANAGE_NOTES' && <FileText size={12} />}
                </span>
                <span className="step-label">[{step.tool}]</span>
                <span className="step-input">{step.input}</span>
                <span className="step-status">➔ {step.status}</span>
              </div>
              {step.output && step.output !== 'null' && step.output !== 'undefined' && step.output.trim().length > 0 && (
                <div className="step-result">
                  {renderTextWithLinks(step.output.substring(0, 300))}
                  {step.output.length > 300 ? '...' : ''}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  )

  // Image File Selection (Deferred Upload)
  const handleSelectFile = (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Create local preview
    const objectUrl = URL.createObjectURL(file)
    setPendingFile(file)
    setPreviewUrl(objectUrl)

    // Reset input so same file can be selected again if needed
    e.target.value = ''
  }

  const removePendingFile = () => {
    setPendingFile(null)
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
  }

  const addToHistory = (type, text) => {
    setConsoleHistory(prev => [...prev, { type, text }])
  }

  const handleClearHistory = () => {
    const freshStart = [
      { type: 'system', text: 'TERMINAL_OS v1.0.1 - History Cleared' },
      { type: 'system', text: 'Ready for new session.' }
    ]
    setConsoleHistory(freshStart)
    localStorage.removeItem('terminal_os_history')
    // No response should be pending
    setIsLoading(false)

    // START NEW SESSION
    const newSid = crypto.randomUUID()
    setSessionId(newSid)
    localStorage.setItem('terminal_os_session_id', newSid)
  }

  const handleConsoleSubmit = async (e) => {
    e.preventDefault()
    if (!consoleInput.trim() && !pendingFile) return

    const input = consoleInput.trim()
    setConsoleInput('')

    // Explicit Clear check before processing anything else
    if (input === '/clear') {
      handleClearHistory()
      return
    }

    // IMAGE UPLOAD SEQUENCE (If file is pending)
    let uploadedImageData = null
    if (pendingFile) {
      addToHistory('input', { text: `> ${input}`, image: previewUrl }) // Show image in history immediately
      setIsLoading(true)

      const formData = new FormData()
      formData.append('file', pendingFile)

      try {
        const upRes = await fetch('/api/vision/upload', { method: 'POST', body: formData })
        if (upRes.ok) {
          uploadedImageData = await upRes.json() // { filename: "...", original: "..." }
        } else {
          addToHistory('system', 'Image upload failed. Sending text only.')
        }
      } catch (e) {
        addToHistory('system', `Upload Error: ${e.message}`)
      }

      // Cleanup local state
      removePendingFile()
    } else if (input) {
      addToHistory('input', `> ${input}`)
    }

    // Command Handling
    if (input.startsWith('/')) {
      const [cmd, ...args] = input.split(' ')

      if (cmd === '/scrape') {
        const url = args[0]
        if (!url) {
          addToHistory('system', 'Usage: /scrape <url>')
          return
        }

        setIsLoading(true)
        addToHistory('system', `Initiating scraping sequence for: ${url}...`)

        try {
          const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
          })

          const data = await response.json()
          if (response.ok) {
            addToHistory('output', `SCRAPE SUCCESS: ${data.title}`)
            addToHistory('output', `DATA: ${data.extracted_data.substring(0, 300)}...`)
          } else {
            addToHistory('system', `Error: ${data.detail}`)
          }
        } catch (err) {
          addToHistory('system', `Connection Error: ${err.message}`)
        } finally {
          setIsLoading(false)
        }
        return
      }

      if (cmd === '/clear') {
        handleClearHistory()
        return
      }
    }

    // Default: Chat with AI (Streaming)
    setIsLoading(true)
    setCurrentActivity("Thinking...")

    // setup AbortController
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortControllerRef.current.signal, // Attach signal
        body: JSON.stringify({
          message: uploadedImageData
            ? `${input}\n(SYSTEM: An image was attached. image_path="${uploadedImageData.filename}". Use vision_analyze immediately to see it.)`
            : input,
          context: buildContext()
            .filter(h => h.type !== 'system')
            .map(h => {
              if (h.type === 'agent-step') {
                const step = h.text || {}
                let resultText = String(step.output || '')
                return {
                  role: 'assistant',
                  content: `[TOOL_EXECUTION] Tool: ${step.tool}, Input: ${step.input}, Result: ${resultText}`
                }
              }
              const contentText = typeof h.text === 'object' ? h.text.text : h.text; // Handle {text, image} objects

              // Ensure we don't send "[object Object]" to backend
              let finalContent = String(contentText || h.content || '').replace('> ', '')
              if (finalContent === '[object Object]') {
                finalContent = JSON.stringify(h.text)
              }

              return {
                role: h.role || (h.type === 'input' ? 'user' : 'assistant'),
                content: finalContent
              }
            }),
          session_id: sessionId
        })
      })

      if (!response.body) throw new Error("ReadableStream not supported")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (value) {
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop()

          for (const line of lines) {
            if (!line.trim()) continue
            try {
              const event = JSON.parse(line)
              processEvent(event)
            } catch (e) {
              console.error("Streaming JSON parse error:", line, e)
            }
          }
        }

        if (done) break
      }

      // Process remaining buffer
      if (buffer.trim()) {
        try {
          const event = JSON.parse(buffer)
          processEvent(event)
        } catch (e) {
          console.error("Final buffer parse error:", buffer, e)
        }
      }

      function processEvent(event) {
        if (event.type === 'info') {
          setCurrentActivity(event.content)
        } else if (event.type === 'thought') {
          const shortThought = event.content.split('\n')[0].substring(0, 50)
          setCurrentActivity(shortThought + "...")
        } else if (event.type === 'step_start') {
          if (event.tool === 'SCRAPE') {
            const url = event.input.length > 30 ? event.input.substring(0, 30) + "..." : event.input
            setCurrentActivity(`Analysing site: ${url}`)
          } else if (event.tool === 'SEARCH') {
            setCurrentActivity(`Searching web: ${event.input}`)
          } else if (event.tool === 'IMAGE_SEARCH') {
            setCurrentActivity(`Searching images: ${event.input}`)
          } else {
            setCurrentActivity(`Running ${event.tool}...`)
          }
        } else if (event.type === 'step_end') {
          addToHistory('agent-step', {
            tool: event.tool,
            input: event.input,
            output: event.output,
            status: event.status
          })
        } else if (event.type === 'final') {
          addToHistory('output', event.content)
        } else if (event.type === 'error') {
          addToHistory('system', event.content)
        }

        if (event.type === 'step_end' && event.tool === 'MANAGE_WALLET') {
          try {
            const output = JSON.parse(event.output)
            if (output.to && output.value) {
              setPendingTx(output)
              setActiveModule('finance')
            }
          } catch (e) { }
        }
      }

    } catch (err) {
      if (err.name === 'AbortError') {
        // Already handled in handleStop usually, but double check
        console.log("Fetch aborted");
      } else {
        addToHistory('system', `Communication Error: ${err.message}`)
      }
    } finally {
      setIsLoading(false)
      setCurrentActivity(null)
      abortControllerRef.current = null;
    }
  }

  // Data Fetching State
  const [events, setEvents] = useState([])
  const [wallet, setWallet] = useState(() => {
    const saved = localStorage.getItem('lain_wallet_addr')
    return { address: saved || null, balance: '0', history: [] }
  })
  // Stats removed
  const [calendarDate, setCalendarDate] = useState(new Date())
  const [selectedDay, setSelectedDay] = useState(null)
  const [pendingTx, setPendingTx] = useState(null)
  const [selectedImage, setSelectedImage] = useState(null)

  // Context Builder for AI
  const buildContext = () => {
    return [
      ...consoleHistory.slice(-100),
      { role: "system", content: `CONNECTED_WALLET: ${wallet.address || 'NONE'}` }
    ]
  }

  // Fetch Data on Module Change
  React.useEffect(() => {
    if (activeModule === 'tasks') fetchEvents()
    if (activeModule === 'finance') fetchWalletData()
    // if (activeModule === 'stats') fetchStats() // Removed

    if (wallet.address) {
      localStorage.setItem('lain_wallet_addr', wallet.address)
    }
  }, [activeModule, wallet.address])

  const fetchEvents = async () => {
    try {
      const res = await fetch('/api/calendar/events')
      const data = await res.json()
      setEvents(data)
    } catch (err) {
      console.error(err)
    }
  }

  const fetchWalletData = async () => {
    if (!wallet.address) return
    try {
      const res = await fetch(`/api/crypto/balance/${wallet.address}`)
      const data = await res.json()
      const histRes = await fetch(`/api/crypto/history/${wallet.address}`)
      const hist = await histRes.json()
      setWallet(prev => ({ ...prev, balance: data.balance, history: hist }))
    } catch (err) {
      console.error(err)
    }
  }

  const connectWallet = async () => {
    if (window.ethereum) {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' })
        setWallet(prev => ({ ...prev, address: accounts[0] }))
        addToHistory('system', `Wallet connected: ${accounts[0]}`)
      } catch (err) {
        addToHistory('system', `MetaMask Error: ${err.message}`)
      }
    } else {
      addToHistory('system', 'MetaMask not found. Please install extension.')
    }
  }

  const signTransaction = async () => {
    if (!pendingTx || !window.ethereum) return
    try {
      addToHistory('system', 'Requesting signature via MetaMask...')
      const txHash = await window.ethereum.request({
        method: 'eth_sendTransaction',
        params: [{
          from: wallet.address,
          to: pendingTx.to,
          value: pendingTx.value,
          gas: pendingTx.gas
        }],
      })
      addToHistory('output', `TRANSACTION SENT: ${txHash}`)
      setPendingTx(null)
      fetchWalletData()
    } catch (err) {
      addToHistory('system', `Signing Failed: ${err.message}`)
    }
  }

  const fetchAccounts = async () => {
    try {
      const res = await fetch('/api/accounts')
      const data = await res.json()
      setEvelineSessions(data)
    } catch (err) {
      console.error(err)
    }
  }

  const fetchDiscordStatus = async () => {
    try {
      const res = await fetch('/api/discord/status')
      const data = await res.json()
      setDiscordStatus(data)
    } catch (err) {
      console.error(err)
    }
  }

  // Poll for accounts & status
  React.useEffect(() => {
    fetchAccounts()
    fetchDiscordStatus()
    const interval = setInterval(() => {
      fetchAccounts()
      fetchDiscordStatus()
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="terminal-os">
      <div className="main-layout">
        {/* Sidebar Navigation */}
        <nav className="sidebar">
          <button
            className={`nav-item ${activeModule === 'console' ? 'active' : ''}`}
            onClick={() => setActiveModule('console')}
          >
            [1] AI_CONSOLE
          </button>
          <button
            className={`nav-item ${activeModule === 'tasks' ? 'active' : ''}`}
            onClick={() => setActiveModule('tasks')}
          >
            [2] CALENDAR
          </button>
          <button
            className={`nav-item ${activeModule === 'finance' ? 'active' : ''}`}
            onClick={() => setActiveModule('finance')}
          >
            [3] CRYPTO_WALLET
          </button>
          <button
            className={`nav-item ${activeModule === 'notes' ? 'active' : ''}`}
            onClick={() => setActiveModule('notes')}
          >
            [4] NOTES_ARCHIVE
          </button>
        </nav>

        {/* Content Area */}
        <main className="content-area">
          {activeModule === 'console' && (
            <div className="module console-module">
              <div className="module-header">
                <div className="header-left">
                  <span>AI_CONSOLE</span>
                  <span className="module-status">ONLINE</span>
                  <div className="discord-status-grid">
                    <div className={`status-node ${discordStatus?.connected ? 'online' : 'offline'}`} title="Discord Connection">
                      <MessageCircle size={10} />
                      <div className="node-glow"></div>
                    </div>
                    <div className={`status-node activity ${discordStatus?.active ? 'active' : ''}`} title="AI Activity">
                      <div className="node-glow"></div>
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  {isLoading && (
                    <button className="header-action-btn stop-btn" onClick={handleStop} title="Stop Task" style={{ background: '#ff4d4d', color: '#fff', border: 'none' }}>
                      <Loader2 size={14} /> STOP
                    </button>
                  )}
                  <button className="header-action-btn" onClick={handleClearHistory} title="Clear Context">
                    <Eraser size={14} /> CLEAR_CHAT
                  </button>
                </div>
              </div>
              <div className="console-output" ref={consoleOutputRef}>
                {(() => {
                  const items = []
                  let currentGroup = null

                  consoleHistory.forEach((entry, idx) => {
                    if (entry.type === 'agent-step') {
                      if (!currentGroup) {
                        currentGroup = { type: 'agent-group', steps: [entry.text], key: idx }
                      } else {
                        currentGroup.steps.push(entry.text)
                      }
                    } else {
                      if (currentGroup) {
                        items.push(renderGroup(currentGroup))
                        currentGroup = null
                      }

                      const textContent = typeof entry.text === 'object' ? entry.text.text : entry.text;
                      const imageContent = entry.image || (typeof entry.text === 'object' ? entry.text.image : null);

                      items.push(
                        <div key={idx} className={`console-line ${entry.type}`}>
                          <span>
                            {entry.type === 'input' ? (
                              renderTextWithLinks(String(textContent || '').replace('> ', ''))
                            ) : (
                              <ReactMarkdown
                                children={String(textContent || '')}
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  code({ node, inline, className, children, ...props }) {
                                    const match = /language-(\w+)/.exec(className || '')
                                    return !inline ? (
                                      <code className={className} style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 4px', borderRadius: '4px' }} {...props}>
                                        {children}
                                      </code>
                                    ) : (
                                      <code className={className} {...props}>
                                        {children}
                                      </code>
                                    )
                                  }
                                }}
                              />
                            )}
                          </span>
                          {/* Image Rendering in History */}
                          {imageContent && (
                            <div className="history-image" style={{ marginTop: '10px' }}>
                              <img
                                src={imageContent}
                                alt="uploaded"
                                style={{ maxWidth: '200px', borderRadius: '4px', border: '1px solid #333', cursor: 'pointer' }}
                                onClick={() => setSelectedImage({ image: imageContent, title: 'Upload', url: imageContent })}
                              />
                            </div>
                          )}
                        </div>
                      )
                    }
                  })

                  if (currentGroup) {
                    items.push(renderGroup(currentGroup))
                  }

                  return items
                })()}

                {isLoading && (
                  <div className="live-activity-box">
                    <div className="box-header">
                      <Loader2 size={14} className="spin icon-yellow" />
                      <span>EVELINE_ACTIVE: {currentActivity?.toUpperCase() || "THINKING..."}</span>
                    </div>
                    <div className="box-visual">
                      <div className="pulse-line"></div>
                      <div className="pulse-line delay-1"></div>
                      <div className="pulse-line delay-2"></div>
                    </div>
                  </div>
                )}
              </div>
              <form onSubmit={handleConsoleSubmit} className="console-input-form-container">
                {previewUrl && (
                  <div className="pending-image-preview">
                    <img src={previewUrl} alt="preview" />
                    <button type="button" onClick={removePendingFile} className="remove-image">
                      <X size={12} />
                    </button>
                  </div>
                )}
                <div className="console-input-form">
                  <span className="prompt">&gt;</span>
                  <input
                    type="text"
                    value={consoleInput}
                    onChange={(e) => setConsoleInput(e.target.value)}
                    className="console-input"
                    placeholder={isLoading ? "PROCESSING..." : "Enter command or chat..."}
                    disabled={isLoading}
                    autoFocus
                  />
                  <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={handleSelectFile}
                  />
                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => fileInputRef.current?.click()}
                    title="Attach Image"
                  >
                    <ImageIcon size={18} />
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Image Lightbox Modal */}
          {selectedImage && (
            <div className="image-modal-overlay" onClick={() => setSelectedImage(null)}>
              <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
                <img src={selectedImage.image} alt={selectedImage.title} />
                <div className="image-modal-info">
                  <h3>{selectedImage.title}</h3>
                  <a href={selectedImage.url} target="_blank" rel="noreferrer">OPEN_SOURCE_URL</a>
                  <button className="close-modal" onClick={() => setSelectedImage(null)}>CLOSE</button>
                </div>
              </div>
            </div>
          )}

          {/* Memory Module Removed */}

          {activeModule === 'tasks' && (
            <div className="module calendar-module">
              <div className="module-header">
                <span>SYSTEM_CALENDAR</span>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <button
                    onClick={() => setCalendarDate(new Date(calendarDate.setMonth(calendarDate.getMonth() - 1)))}
                    style={{ background: '#333', border: 'none', color: '#fff', padding: '2px 8px', borderRadius: '4px', cursor: 'pointer' }}
                  >&lt;</button>
                  <span style={{ minWidth: '120px', textAlign: 'center' }}>
                    {calendarDate.toLocaleString('default', { month: 'long', year: 'numeric' }).toUpperCase()}
                  </span>
                  <button
                    onClick={() => setCalendarDate(new Date(calendarDate.setMonth(calendarDate.getMonth() + 1)))}
                    style={{ background: '#333', border: 'none', color: '#fff', padding: '2px 8px', borderRadius: '4px', cursor: 'pointer' }}
                  >&gt;</button>
                </div>
                <span className="module-status">{events.length} EVENTS</span>
              </div>
              <div className="calendar-container">
                <div className="calendar-grid" style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(7, 1fr)',
                  gap: '5px',
                  background: 'rgba(0,0,0,0.2)',
                  padding: '10px',
                  borderRadius: '4px'
                }}>
                  {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map(d => (
                    <div key={d} style={{ textAlign: 'center', fontWeight: 'bold', fontSize: '0.8rem', padding: '5px', color: '#666' }}>{d}</div>
                  ))}
                  {(() => {
                    const year = calendarDate.getFullYear();
                    const month = calendarDate.getMonth();
                    const firstDay = new Date(year, month, 1).getDay();
                    const daysInMonth = new Date(year, month + 1, 0).getDate();
                    const startOffset = (firstDay === 0 ? 6 : firstDay - 1); // Adjust for Monday start

                    return [...Array(42)].map((_, i) => {
                      const dayNum = i - startOffset + 1;
                      const isCurrentMonth = dayNum > 0 && dayNum <= daysInMonth;

                      return (
                        <div key={i}
                          onClick={() => isCurrentMonth && setSelectedDay({ day: dayNum, month, year })}
                          style={{
                            minHeight: '80px',
                            background: isCurrentMonth ? 'rgba(255,255,255,0.03)' : 'transparent',
                            border: selectedDay?.day === dayNum && selectedDay?.month === month ? '1px solid #00ff7f' : '1px solid rgba(255,255,255,0.05)',
                            padding: '5px',
                            fontSize: '0.7rem',
                            position: 'relative',
                            opacity: isCurrentMonth ? 1 : 0.2,
                            cursor: isCurrentMonth ? 'pointer' : 'default'
                          }}>
                          {isCurrentMonth && (
                            <>
                              <span style={{ opacity: 0.3 }}>{dayNum}</span>
                              <div className="day-events">
                                {events.filter(e => {
                                  const eventDate = new Date(e.start);
                                  const isSameDay = (d1, d2Year, d2Month, d2Day) => {
                                    return d1.getFullYear() === d2Year &&
                                      d1.getMonth() === d2Month &&
                                      d1.getDate() === d2Day;
                                  };
                                  return isSameDay(eventDate, year, month, dayNum);
                                }).map(e => (
                                  <div key={e.id} style={{
                                    background: 'rgba(0, 255, 127, 0.2)',
                                    borderLeft: '2px solid #00ff7f',
                                    padding: '2px 4px',
                                    marginBottom: '2px',
                                    borderRadius: '2px',
                                    fontSize: '0.65rem',
                                    overflow: 'hidden',
                                    whiteSpace: 'nowrap',
                                    textOverflow: 'ellipsis'
                                  }}>
                                    {e.title}
                                  </div>
                                ))}
                              </div>
                            </>
                          )}
                        </div>
                      );
                    });
                  })()}
                </div>
                {selectedDay && (
                  <div className="event-details-overlay" style={{
                    marginTop: '20px',
                    background: 'rgba(0, 255, 127, 0.05)',
                    border: '1px solid rgba(0, 255, 127, 0.2)',
                    padding: '20px',
                    borderRadius: '4px',
                    animation: 'fadeIn 0.3s ease'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                      <h3 style={{ margin: 0, color: '#00ff7f' }}>
                        DETAILS: {selectedDay.day}/{selectedDay.month + 1}/{selectedDay.year}
                      </h3>
                      <button
                        onClick={() => setSelectedDay(null)}
                        style={{ background: 'transparent', border: 'none', color: '#666', cursor: 'pointer' }}
                      >[CLOSE]</button>
                    </div>

                    {events.filter(e => {
                      const d = new Date(e.start);
                      return d.getFullYear() === selectedDay.year && d.getMonth() === selectedDay.month && d.getDate() === selectedDay.day;
                    }).length === 0 ? (
                      <p style={{ opacity: 0.5 }}>No events scheduled for this day.</p>
                    ) : (
                      <div style={{ display: 'grid', gap: '15px' }}>
                        {events.filter(e => {
                          const d = new Date(e.start);
                          return d.getFullYear() === selectedDay.year && d.getMonth() === selectedDay.month && d.getDate() === selectedDay.day;
                        }).map(e => (
                          <div key={e.id} style={{ background: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '4px', border: '1px solid #333' }}>
                            <div style={{ fontWeight: 'bold', fontSize: '1.1rem', marginBottom: '5px' }}>{e.title}</div>
                            <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr', fontSize: '0.9rem', gap: '5px' }}>
                              <span style={{ opacity: 0.5 }}>TIME:</span>
                              <span>{new Date(e.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>

                              <span style={{ opacity: 0.5 }}>LOCATION:</span>
                              <span>{e.location || 'Not specified'}</span>

                              <span style={{ opacity: 0.5 }}>INFO:</span>
                              <span style={{ whiteSpace: 'pre-wrap' }}>{e.description || 'No additional details.'}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="event-list" style={{ marginTop: '20px' }}>
                  <h3 style={{ fontSize: '0.9rem', marginBottom: '10px', color: '#00ff7f' }}>Upcoming Details</h3>
                  {events.slice(0, 5).map(e => (
                    <div key={e.id} style={{ background: 'rgba(255,255,255,0.02)', padding: '10px', borderRadius: '4px', marginBottom: '5px', border: '1px solid #222' }}>
                      <div style={{ fontWeight: 'bold' }}>{e.title}</div>
                      <div style={{ fontSize: '0.8rem', opacity: 0.6 }}>{new Date(e.start).toLocaleString()} - {e.location || 'No location'}</div>
                      <div style={{ fontSize: '0.8rem', marginTop: '5px' }}>{e.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeModule === 'finance' && (
            <div className="module crypto-module">
              <div className="module-header">
                <span>CRYPTO_WALLET</span>
                <span className="module-status">{wallet.address ? 'CONNECTED' : 'WAITING'}</span>
              </div>
              <div className="wallet-content">
                {!wallet.address ? (
                  <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Wallet size={48} style={{ marginBottom: '20px', opacity: 0.3 }} />
                    <h3>No Wallet Connected</h3>
                    <p style={{ opacity: 0.6, marginBottom: '20px' }}>Connect MetaMask to enable crypto features.</p>
                    <button
                      onClick={connectWallet}
                      className="header-action-btn"
                      style={{ padding: '10px 20px', fontSize: '1rem', background: '#00ff7f', color: '#000' }}
                    >
                      CONNECT_METAMASK
                    </button>
                  </div>
                ) : (
                  <div className="wallet-dashboard">
                    {pendingTx && (
                      <div className="pending-tx-alert" style={{
                        background: 'rgba(255, 255, 0, 0.1)',
                        border: '1px solid #ffff00',
                        padding: '15px',
                        borderRadius: '4px',
                        marginBottom: '20px'
                      }}>
                        <div style={{ color: '#ffff00', fontWeight: 'bold', marginBottom: '10px' }}>⚠️ PENDING_AUTHORIZATION</div>
                        <p style={{ fontSize: '0.9rem', marginBottom: '15px' }}>
                          Eveline proposes a transfer of <strong>{ethers.formatEther(pendingTx.value)} ETH</strong> to <br />
                          <code style={{ fontSize: '0.8rem', opacity: 0.8 }}>{pendingTx.to}</code>
                        </p>
                        <div style={{ display: 'flex', gap: '10px' }}>
                          <button
                            onClick={signTransaction}
                            style={{ background: '#ffff00', color: '#000', border: 'none', padding: '8px 15px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                          >
                            SIGN_&_SEND
                          </button>
                          <button
                            onClick={() => setPendingTx(null)}
                            style={{ background: 'transparent', color: '#fff', border: '1px solid #444', padding: '8px 15px', borderRadius: '4px', cursor: 'pointer' }}
                          >
                            REJECT
                          </button>
                        </div>
                      </div>
                    )}
                    <div className="wallet-card" style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '8px', border: '1px solid #333', marginBottom: '20px' }}>
                      <div style={{ fontSize: '0.8rem', opacity: 0.5, marginBottom: '5px' }}>AVAILABLE_BALANCE</div>
                      <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00ff7f' }}>{parseFloat(wallet.balance).toFixed(4)} ETH</div>
                      <div style={{ fontSize: '0.8rem', marginTop: '10px', wordBreak: 'break-all', opacity: 0.7 }}>
                        <span style={{ color: '#00ff7f' }}>ADDR:</span> {wallet.address}
                      </div>
                    </div>

                    <div className="transaction-history">
                      <h3 style={{ fontSize: '1rem', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ArrowRightLeft size={16} /> RECENT_TRANSACTIONS
                      </h3>
                      <table className="data-grid">
                        <thead>
                          <tr>
                            <th>TYPE</th>
                            <th>VALUE</th>
                            <th>STATUS</th>
                            <th>DATE</th>
                          </tr>
                        </thead>
                        <tbody>
                          {wallet.history.map((tx, idx) => (
                            <tr key={idx}>
                              <td style={{ color: tx.from.toLowerCase() === wallet.address.toLowerCase() ? '#ff4d4d' : '#00ff7f' }}>
                                {tx.from.toLowerCase() === wallet.address.toLowerCase() ? 'SEND' : 'RECEIVE'}
                              </td>
                              <td>{tx.value}</td>
                              <td style={{ opacity: 0.6 }}>{tx.status.toUpperCase()}</td>
                              <td>{tx.date}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SYSTEM STATS REMOVED */}

          {activeModule === 'notes' && (
            <div className="module notes-module">
              <div className="module-header">
                <div className="header-left">
                  <FileText size={16} />
                  <span>NOTES_ARCHIVE</span>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button onClick={fetchNotes} className="header-action-btn">REFRESH</button>
                </div>
              </div>
              <div className="notes-content">
                {notes.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px', opacity: 0.5 }}>
                    <FileText size={48} style={{ marginBottom: '20px', opacity: 0.3 }} />
                    <p>No notes found. Ask Eveline to save something!</p>
                  </div>
                ) : (
                  <div className="notes-grid-view">
                    {notes.filter(n => n.category !== 'AI_INTERNAL').map(note => (
                      <div
                        key={note.id}
                        className="note-card"
                        onClick={() => setSelectedNote(note)}
                        style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                      >
                        <div className="note-card-header">
                          <span className="note-category">[{note.category}]</span>
                          <span className="note-date">{new Date(note.created_at).toLocaleDateString()}</span>
                        </div>
                        <h3 className="note-title">{note.title}</h3>
                        <p className="note-body">{note.content.substring(0, 150)}{note.content.length > 150 ? '...' : ''}</p>
                        {note.tags && (
                          <div className="note-tags">
                            {note.tags.split(',').map((tag, i) => (
                              <span key={i} className="note-tag">#{tag.trim()}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Note Detail Modal */}
          {selectedNote && (
            <div className="image-modal-overlay" onClick={() => setSelectedNote(null)}>
              <div
                className="note-modal-content"
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ borderBottom: '1px solid #333', paddingBottom: '15px', marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h2 style={{ margin: 0, color: '#fff' }}>{selectedNote.title}</h2>
                    <span style={{ fontSize: '0.8rem', opacity: 0.6 }}>{new Date(selectedNote.created_at).toLocaleString()}</span>
                  </div>
                  <button onClick={() => setSelectedNote(null)} style={{ background: 'transparent', border: 'none', color: '#666', cursor: 'pointer' }}>[CLOSE]</button>
                </div>

                <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', color: '#ccc', marginBottom: '20px' }}>
                  {selectedNote.content}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', borderTop: '1px solid #333', paddingTop: '15px' }}>
                  <button
                    onClick={() => downloadSingleNote(selectedNote)}
                    className="header-action-btn"
                    style={{ borderColor: 'var(--accent-green)', color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <Download size={14} /> DOWNLOAD_TXT
                  </button>
                </div>
              </div>
            </div>
          )}
          {/* Live Feed Removed */}
        </main>

        {/* Motivational Panel */}
        <aside className="motivation-panel">
          <img src={motivationImg} alt="Stay motivated" />
          {/* macOS-style Status Indicators */}
          <div className="status-dots">
            <div className="dot-group">
              <span className="dot dot-red"></span>
              <span className="dot dot-yellow"></span>
              <span className="dot dot-green"></span>
            </div>
          </div>

          <div className="system-stats">
            <div className="stat-row">
              <span className="stat-key">TIME</span>
              <span className="stat-val">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default App
