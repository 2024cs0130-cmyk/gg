'use client'

import { useState } from 'react'
import { Code2, Users, Building2, Eye, EyeOff, ArrowRight, Zap, AlertTriangle, TrendingUp, GitCommit, Shield, Activity } from 'lucide-react'

type Role = 'developer' | 'manager' | 'ceo'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<Role>('developer')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Invalid credentials')
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('role', data.role)
      localStorage.setItem('org_id', data.org_id)
      localStorage.setItem('display_name', data.display_name)
      document.cookie = `token=${data.access_token}; path=/`
      window.location.href = `/dashboard/${data.role}`
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const roles = [
    { id: 'developer' as Role, label: 'Developer', icon: Code2, desc: 'View your scores' },
    { id: 'manager' as Role, label: 'Manager', icon: Users, desc: 'Monitor your team' },
    { id: 'ceo' as Role, label: 'CEO', icon: Building2, desc: 'Org intelligence' },
  ]

  return (
    <>
      <style>{`
        *{margin:0;padding:0;box-sizing:border-box;}
        html,body,#__next{width:100%;height:100%;overflow:hidden;}
        @keyframes fa{0%,100%{transform:rotate(-2deg) translateY(0)}50%{transform:rotate(-2deg) translateY(-8px)}}
        @keyframes fb{0%,100%{transform:rotate(1.5deg) translateY(0)}50%{transform:rotate(1.5deg) translateY(-6px)}}
        @keyframes fc{0%,100%{transform:rotate(-1deg) translateY(0)}50%{transform:rotate(-1deg) translateY(-8px)}}
        @keyframes fd{0%,100%{transform:rotate(0.8deg) translateY(0)}50%{transform:rotate(0.8deg) translateY(-5px)}}
        @keyframes spin{to{transform:rotate(360deg)}}
        @keyframes pulse{0%,100%{opacity:1;box-shadow:0 0 14px rgba(99,102,241,0.9)}50%{opacity:0.7;box-shadow:0 0 6px rgba(99,102,241,0.4)}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
        .a1{animation:fadeIn 0.45s 0s ease both;}
        .a2{animation:fadeIn 0.45s 0.08s ease both;}
        .a3{animation:fadeIn 0.45s 0.16s ease both;}
        .a4{animation:fadeIn 0.45s 0.24s ease both;}
        .a5{animation:fadeIn 0.45s 0.32s ease both;}
        input::placeholder{color:#2e2e3e;}
        input:focus{border-color:#6366f1!important;outline:none;box-shadow:0 0 0 3px rgba(99,102,241,0.1)!important;}
        .rb:hover{border-color:#2e2e42!important;}
        .sb:hover:not(:disabled){background:#4f46e5!important;transform:translateY(-1px);}
        .cr:hover .ce{color:#a5b4fc!important;}
      `}</style>

      <div style={{position:'fixed',inset:0,display:'flex',background:'#07070e',fontFamily:'-apple-system,system-ui,sans-serif'}}>

        {/* -- LEFT PANEL - fills full height -- */}
        <div style={{flex:'0 0 58%',position:'relative',overflow:'hidden',borderRight:'1px solid #111120',display:'flex',flexDirection:'column',padding:'0'}}>

          {/* grid bg */}
          <div style={{position:'absolute',inset:0,backgroundImage:'linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px)',backgroundSize:'50px 50px',pointerEvents:'none'}}/>

          {/* orbs */}
          <div style={{position:'absolute',top:'-20%',left:'-10%',width:'55%',height:'55%',background:'radial-gradient(circle,rgba(99,102,241,0.07) 0%,transparent 65%)',pointerEvents:'none'}}/>
          <div style={{position:'absolute',bottom:'-10%',right:'5%',width:'40%',height:'40%',background:'radial-gradient(circle,rgba(34,197,94,0.04) 0%,transparent 65%)',pointerEvents:'none'}}/>
          <div style={{position:'absolute',top:'40%',right:'-5%',width:'30%',height:'30%',background:'radial-gradient(circle,rgba(245,158,11,0.03) 0%,transparent 65%)',pointerEvents:'none'}}/>

          {/* TOP -- logo + headline */}
          <div style={{padding:'36px 52px 0',position:'relative',zIndex:2}}>
            <div className="a1" style={{display:'flex',alignItems:'center',gap:'10px',marginBottom:'40px'}}>
              <div style={{display:'flex',alignItems:'center',gap:'7px'}}>
                <div style={{width:'9px',height:'9px',borderRadius:'50%',background:'#6366f1',animation:'pulse 2.5s ease-in-out infinite'}}/>
                <span style={{color:'#fafafa',fontSize:'17px',fontWeight:'600',letterSpacing:'-0.4px'}}>DevIQ</span>
              </div>
              <span style={{background:'rgba(99,102,241,0.1)',border:'1px solid rgba(99,102,241,0.2)',color:'#a5b4fc',fontSize:'10px',fontWeight:'500',padding:'2px 8px',borderRadius:'20px',letterSpacing:'0.07em'}}>BETA</span>
            </div>

            <div className="a2">
              <h2 style={{color:'#fafafa',fontSize:'clamp(24px,2.8vw,40px)',fontWeight:'600',letterSpacing:'-1.5px',lineHeight:1.08,margin:'0 0 12px'}}>
                Every commit.<br/>
                <span style={{color:'#6366f1'}}>Scored</span> in real time.
              </h2>
              <p style={{color:'#404055',fontSize:'13px',lineHeight:1.65,maxWidth:'360px'}}>
                Developer intelligence platform - translate code to meaning, surface what actually matters.
              </p>
            </div>
          </div>

          {/* MIDDLE -- cards spread evenly */}
          <div style={{flex:1,position:'relative',zIndex:2,display:'grid',gridTemplateColumns:'1fr 1fr',gridTemplateRows:'1fr 1fr',gap:'16px',padding:'28px 52px'}}>

            {/* card 1 -- effort score */}
            <div style={{background:'#0c0c1a',border:'1px solid #1a1a2c',borderTop:'3px solid #6366f1',borderRadius:'14px',padding:'20px 22px',animation:'fa 5s ease-in-out infinite',boxShadow:'0 8px 32px rgba(0,0,0,0.5)',alignSelf:'center'}}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'10px'}}>
                <span style={{color:'#6366f1',fontSize:'10px',fontWeight:'600',letterSpacing:'0.1em',textTransform:'uppercase'}}>Effort score</span>
                <Zap size={12} color="#6366f1"/>
              </div>
              <div style={{display:'flex',alignItems:'baseline',gap:'3px',marginBottom:'6px'}}>
                <span style={{color:'#fafafa',fontSize:'36px',fontWeight:'700',letterSpacing:'-2px',lineHeight:1}}>84</span>
                <span style={{color:'#252535',fontSize:'18px'}}>/100</span>
              </div>
              <p style={{color:'#a1a1aa',fontSize:'12px',margin:'0 0 3px'}}>Rajan Kumar</p>
              <p style={{color:'#303040',fontSize:'11px',fontFamily:'monospace'}}>Login endpoint · 2 min ago</p>
              <div style={{marginTop:'10px',background:'#13131f',borderRadius:'3px',height:'3px',overflow:'hidden'}}>
                <div style={{background:'#6366f1',width:'84%',height:'100%',borderRadius:'3px'}}/>
              </div>
            </div>

            {/* card 2 -- silent blocker */}
            <div style={{background:'#0c0c1a',border:'1px solid #1a1a2c',borderTop:'3px solid #f59e0b',borderRadius:'14px',padding:'20px 22px',animation:'fb 5s ease-in-out infinite 1.8s',boxShadow:'0 8px 32px rgba(0,0,0,0.5)',alignSelf:'center',marginTop:'20px'}}>
              <div style={{display:'flex',alignItems:'center',gap:'7px',marginBottom:'10px'}}>
                <AlertTriangle size={12} color="#f59e0b"/>
                <span style={{color:'#f59e0b',fontSize:'10px',fontWeight:'600',letterSpacing:'0.1em',textTransform:'uppercase'}}>Silent blocker</span>
              </div>
              <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 4px'}}>Priya -- DEV-142</p>
              <p style={{color:'#71717a',fontSize:'11px',margin:'0 0 10px'}}>52 hours with no commits</p>
              <div style={{background:'#13131f',borderRadius:'3px',height:'3px',overflow:'hidden'}}>
                <div style={{background:'#f59e0b',width:'87%',height:'100%'}}/>
              </div>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginTop:'8px'}}>
                <span style={{color:'#52525b',fontSize:'10px'}}>DEV-142 · In progress</span>
                <span style={{background:'rgba(245,158,11,0.1)',color:'#f59e0b',fontSize:'10px',padding:'1px 6px',borderRadius:'20px'}}>High risk</span>
              </div>
            </div>

            {/* card 3 -- team health */}
            <div style={{background:'#0c0c1a',border:'1px solid #1a1a2c',borderTop:'3px solid #22c55e',borderRadius:'14px',padding:'20px 22px',animation:'fc 5s ease-in-out infinite 3.5s',boxShadow:'0 8px 32px rgba(0,0,0,0.5)',alignSelf:'center',marginTop:'-20px'}}>
              <div style={{display:'flex',alignItems:'center',gap:'7px',marginBottom:'10px'}}>
                <TrendingUp size={12} color="#22c55e"/>
                <span style={{color:'#22c55e',fontSize:'10px',fontWeight:'600',letterSpacing:'0.1em',textTransform:'uppercase'}}>Team health</span>
              </div>
              <div style={{display:'flex',alignItems:'baseline',gap:'4px',marginBottom:'10px'}}>
                <span style={{color:'#fafafa',fontSize:'36px',fontWeight:'700',letterSpacing:'-1.5px',lineHeight:1}}>91</span>
                <span style={{color:'#252535',fontSize:'18px'}}>%</span>
                <span style={{color:'#22c55e',fontSize:'11px',marginLeft:'4px'}}>↑ +4</span>
              </div>
              <div style={{display:'flex',flexDirection:'column',gap:'5px'}}>
                {[{l:'Arjun',v:91,c:'#22c55e'},{l:'Rajan',v:84,c:'#6366f1'},{l:'Karan',v:78,c:'#a78bfa'}].map((d,i)=>(
                  <div key={i} style={{display:'flex',alignItems:'center',gap:'8px'}}>
                    <span style={{color:'#52525b',fontSize:'10px',width:'36px'}}>{d.l}</span>
                    <div style={{flex:1,background:'#13131f',borderRadius:'2px',height:'3px'}}><div style={{background:d.c,width:`${d.v}%`,height:'100%',borderRadius:'2px'}}/></div>
                    <span style={{color:'#52525b',fontSize:'10px',fontFamily:'monospace',width:'20px',textAlign:'right'}}>{d.v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* card 4 -- live commits */}
            <div style={{background:'#0c0c1a',border:'1px solid #1a1a2c',borderTop:'3px solid #8b5cf6',borderRadius:'14px',padding:'20px 22px',animation:'fd 5s ease-in-out infinite 2.6s',boxShadow:'0 8px 32px rgba(0,0,0,0.5)',alignSelf:'center'}}>
              <div style={{display:'flex',alignItems:'center',gap:'7px',marginBottom:'12px'}}>
                <GitCommit size={12} color="#8b5cf6"/>
                <span style={{color:'#8b5cf6',fontSize:'10px',fontWeight:'600',letterSpacing:'0.1em',textTransform:'uppercase'}}>Live pipeline</span>
                <div style={{marginLeft:'auto',width:'6px',height:'6px',borderRadius:'50%',background:'#22c55e',boxShadow:'0 0 6px #22c55e'}}/>
              </div>
              {[{sha:'ea70c19',dev:'rajan',score:84,c:'#22c55e'},{sha:'3f2a891',dev:'arjun',score:91,c:'#22c55e'},{sha:'c92b334',dev:'priya',score:23,c:'#ef4444'}].map((c,i)=>(
                <div key={i} style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'5px 0',borderBottom:i<2?'1px solid #111120':'none'}}>
                  <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
                    <span style={{color:'#303045',fontSize:'10px',fontFamily:'monospace'}}>{c.sha}</span>
                    <span style={{color:'#71717a',fontSize:'11px'}}>{c.dev}</span>
                  </div>
                  <span style={{color:c.c,fontSize:'12px',fontWeight:'600',fontFamily:'monospace'}}>{c.score}</span>
                </div>
              ))}
            </div>
          </div>

          {/* BOTTOM -- stats */}
          <div style={{padding:'0 52px 32px',position:'relative',zIndex:2}}>
            <div className="a3" style={{display:'flex',gap:'32px',paddingTop:'16px',borderTop:'1px solid #111120'}}>
              {[{v:'10k+',l:'commits scored'},{v:'<30s',l:'score latency'},{v:'3',l:'role dashboards'},{v:'100%',l:'automated'}].map((s,i)=>(
                <div key={i}>
                  <p style={{color:'#fafafa',fontSize:'15px',fontWeight:'600',margin:'0 0 2px',letterSpacing:'-0.5px'}}>{s.v}</p>
                  <p style={{color:'#303040',fontSize:'11px',margin:0}}>{s.l}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* -- RIGHT PANEL - full height form -- */}
        <div style={{flex:'0 0 42%',display:'flex',flexDirection:'column',justifyContent:'center',background:'#07070e',padding:'0 52px',position:'relative',overflow:'hidden'}}>

          {/* subtle right orb */}
          <div style={{position:'absolute',top:'-20%',right:'-20%',width:'60%',height:'60%',background:'radial-gradient(circle,rgba(99,102,241,0.04) 0%,transparent 65%)',pointerEvents:'none'}}/>

          <div style={{width:'100%',maxWidth:'400px',margin:'0 auto',position:'relative',zIndex:2}}>

            <div className="a1" style={{marginBottom:'32px'}}>
              <h1 style={{color:'#fafafa',fontSize:'24px',fontWeight:'600',letterSpacing:'-0.8px',margin:'0 0 6px'}}>Welcome back</h1>
              <p style={{color:'#71717a',fontSize:'13px',margin:0}}>Sign in to your DevIQ workspace</p>
            </div>

            <div className="a2" style={{marginBottom:'14px'}}>
              <label style={{display:'block',color:'#a1a1aa',fontSize:'12px',fontWeight:'500',marginBottom:'7px'}}>Email address</label>
              <input type="email" placeholder="name@company.com" value={email} onChange={e=>setEmail(e.target.value)}
                style={{display:'block',width:'100%',height:'44px',background:'#0e0e1c',border:'1px solid #1a1a2c',borderRadius:'10px',padding:'0 14px',color:'#fafafa',fontSize:'14px',transition:'all 0.15s'}}/>
            </div>

            <div className="a2" style={{marginBottom:'20px'}}>
              <label style={{display:'block',color:'#a1a1aa',fontSize:'12px',fontWeight:'500',marginBottom:'7px'}}>Password</label>
              <div style={{position:'relative'}}>
                <input type={showPassword?'text':'password'} placeholder="••••••••" value={password} onChange={e=>setPassword(e.target.value)} onKeyDown={e=>e.key==='Enter'&&handleLogin()}
                  style={{display:'block',width:'100%',height:'44px',background:'#0e0e1c',border:'1px solid #1a1a2c',borderRadius:'10px',padding:'0 44px 0 14px',color:'#fafafa',fontSize:'14px',transition:'all 0.15s'}}/>
                <button onClick={()=>setShowPassword(!showPassword)} style={{position:'absolute',right:'13px',top:'50%',transform:'translateY(-50%)',background:'none',border:'none',cursor:'pointer',color:'#52525b',padding:0,display:'flex',alignItems:'center'}}>
                  {showPassword?<EyeOff size={15}/>:<Eye size={15}/>} 
                </button>
              </div>
            </div>

            <div className="a3" style={{marginBottom:'22px'}}>
              <label style={{display:'block',color:'#a1a1aa',fontSize:'12px',fontWeight:'500',marginBottom:'10px'}}>Sign in as</label>
              <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:'8px'}}>
                {roles.map(r=>{
                  const Icon=r.icon;const sel=role===r.id
                  return(
                    <button key={r.id} className="rb" onClick={()=>setRole(r.id)} style={{padding:'14px 8px',cursor:'pointer',transition:'all 0.15s',background:sel?'rgba(99,102,241,0.09)':'#0e0e1c',border:`1px solid ${sel?'#6366f1':'#1a1a2c'}`,borderRadius:'10px',display:'flex',flexDirection:'column',alignItems:'center',gap:'6px'}}>
                      <Icon size={16} color={sel?'#6366f1':'#52525b'}/>
                      <span style={{color:sel?'#a5b4fc':'#71717a',fontSize:'11px',fontWeight:'500'}}>{r.label}</span>
                      <span style={{color:sel?'#6366f1':'#252535',fontSize:'10px'}}>{r.desc}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {error&&(
              <div style={{background:'rgba(239,68,68,0.07)',border:'1px solid rgba(239,68,68,0.18)',borderRadius:'10px',padding:'11px 14px',marginBottom:'16px'}}>
                <p style={{color:'#f87171',fontSize:'13px',margin:0}}>{error}</p>
              </div>
            )}

            <div className="a4">
              <button className="sb" onClick={handleLogin} disabled={loading} style={{display:'flex',alignItems:'center',justifyContent:'center',gap:'8px',width:'100%',height:'44px',background:'#6366f1',border:'none',borderRadius:'10px',color:'#fff',fontSize:'14px',fontWeight:'500',cursor:loading?'wait':'pointer',transition:'all 0.15s',marginBottom:'20px'}}>
                {loading?<div style={{width:'16px',height:'16px',border:'2px solid rgba(255,255,255,0.2)',borderTopColor:'#fff',borderRadius:'50%',animation:'spin 0.7s linear infinite'}}/>:<><span>Sign in</span><ArrowRight size={14}/></>}
              </button>
            </div>

            <div className="a4" style={{borderTop:'1px solid #111120',paddingTop:'18px',marginBottom:'16px'}}>
              <p style={{color:'#252535',fontSize:'12px',textAlign:'center'}}>Don't have an account? <span style={{color:'#3f3f46'}}>Contact your admin</span></p>
            </div>

            <div className="a5" style={{background:'#0a0a18',border:'1px solid #14142a',borderRadius:'12px',padding:'14px 16px'}}>
              <p style={{color:'#303048',fontSize:'10px',fontWeight:'600',margin:'0 0 10px',letterSpacing:'0.1em',textTransform:'uppercase'}}>Quick test logins -- click to fill</p>
              <div style={{display:'flex',flexDirection:'column',gap:'2px'}}>
                {[{e:'developer@deviq.test',p:'DevTest123!',c:'#6366f1',r:'Dev'},{e:'manager@deviq.test',p:'MgrTest123!',c:'#22c55e',r:'Mgr'},{e:'ceo@deviq.test',p:'CeoTest123!',c:'#f59e0b',r:'CEO'}].map((c,i)=>(
                  <button key={i} className="cr" onClick={()=>{setEmail(c.e);setPassword(c.p)}} style={{display:'flex',alignItems:'center',justifyContent:'space-between',width:'100%',background:'none',border:'none',cursor:'pointer',padding:'6px 0',borderBottom:i<2?'1px solid #111120':'none'}}>
                    <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
                      <span style={{background:`${c.c}18`,color:c.c,fontSize:'9px',fontWeight:'600',padding:'2px 6px',borderRadius:'4px'}}>{c.r}</span>
                      <span className="ce" style={{color:'#52525b',fontSize:'11px',fontFamily:'monospace',transition:'color 0.15s'}}>{c.e}</span>
                    </div>
                    <span style={{color:'#252535',fontSize:'10px',fontFamily:'monospace'}}>{c.p}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
