'use client'
import { useState } from 'react'
import { Users, Bell, UserCheck, GitMerge, LogOut, TrendingUp, TrendingDown, AlertTriangle, Clock, CheckCircle, Search, X } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, Cell } from 'recharts'

const DEVS = [
  {name:'Rajan Kumar',user:'rajan',score:89,prev:84,confidence:'high',relevance:0.92,impact:0.86,complexity:0.8,glue:0.69,explanation:'Stabilized payment retries and fixed flaky checkout tests.',burnout:false,ticket:'PAY-214',lastCommit:'2h ago'},
  {name:'Priya Sharma',user:'priya',score:78,prev:74,confidence:'high',relevance:0.82,impact:0.75,complexity:0.79,glue:0.71,explanation:'Improved OAuth token refresh flow and reduced auth errors.',burnout:false,ticket:'AUTH-112',lastCommit:'4h ago'},
  {name:'Arjun Malhothra',user:'arjun',score:62,prev:70,confidence:'medium',relevance:0.72,impact:0.61,complexity:0.84,glue:0.53,explanation:'Delivered mobile sync patch but currently carrying blocker load.',burnout:true,ticket:'MOB-88',lastCommit:'1d ago'},
  {name:'Karan Patel',user:'karan',score:93,prev:90,confidence:'high',relevance:0.95,impact:0.91,complexity:0.88,glue:0.64,explanation:'Shipped search ranking update with measurable engagement gains.',burnout:false,ticket:'SRCH-301',lastCommit:'3h ago'},
  {name:'Meera Iyer',user:'meera',score:84,prev:81,confidence:'high',relevance:0.87,impact:0.79,complexity:0.76,glue:0.9,explanation:'Led frontend migration and supported cross-team release.',burnout:false,ticket:'UI-209',lastCommit:'6h ago'},
]
const ALERTS: Array<{ id: string; type: string; dev: string; msg: string; sev: string }> = [
  {id:'a1',type:'burnout',dev:'Arjun Malhothra',msg:'High activity for 9 days with score decline.',sev:'high'},
  {id:'a2',type:'blocker',dev:'Priya Sharma',msg:'Waiting on infra secret rotation for AUTH-112.',sev:'medium'},
  {id:'a3',type:'dependency',dev:'Meera Iyer',msg:'Frontend release depends on API schema freeze.',sev:'medium'},
]
const TREND = [
  {week:'W1',rajan:74,arjun:66,priya:70,karan:76,meera:72},
  {week:'W2',rajan:78,arjun:69,priya:71,karan:79,meera:74},
  {week:'W3',rajan:81,arjun:71,priya:73,karan:82,meera:76},
  {week:'W4',rajan:83,arjun:68,priya:75,karan:85,meera:78},
  {week:'W5',rajan:85,arjun:66,priya:76,karan:88,meera:80},
  {week:'W6',rajan:86,arjun:63,priya:77,karan:90,meera:81},
  {week:'W7',rajan:88,arjun:61,priya:78,karan:92,meera:83},
  {week:'W8',rajan:89,arjun:62,priya:78,karan:93,meera:84},
]
const BARS = DEVS.map(d=>({name:d.name.split(' ')[0],score:d.score}))
const BAR_COLORS = ['#6366f1','#22c55e','#ef4444','#f59e0b','#8b5cf6','#06b6d4']

const T2 = ({active,payload,label}:any)=>active&&payload?.length?<div style={{background:'#161616',border:'1px solid #262626',borderRadius:'8px',padding:'10px 12px'}}><p style={{color:'#a1a1aa',fontSize:'11px',margin:'0 0 6px'}}>{label}</p>{payload.map((p:any,i:number)=><p key={i} style={{color:p.color,fontSize:'12px',margin:'2px 0'}}>{p.name}: {p.value}</p>)}</div>:null

export default function ManagerDash() {
  const [tab,setTab]=useState('overview')
  const [dismissed,setDismissed]=useState<string[]>([])
  const [matchQ,setMatchQ]=useState('')
  const [matchRes,setMatchRes]=useState<any[]|null>(null)
  const name=typeof window!=='undefined'?localStorage.getItem('display_name')||'Manager':'Manager'
  const active=ALERTS.filter(a=>!dismissed.includes(a.id))
  const teamAvg=Math.round(DEVS.reduce((a,b)=>a+b.score,0)/DEVS.length)
  const nav=[{icon:Users,label:'Team Overview',id:'overview'},{icon:Bell,label:'Alerts',id:'alerts'},{icon:UserCheck,label:'Dev Profiles',id:'profiles'},{icon:GitMerge,label:'Project Match',id:'match'}]
  const handleMatch=()=>{const r=DEVS.map(d=>({...d,match:Math.floor(60+Math.random()*35)})).sort((a,b)=>b.match-a.match);setMatchRes(r)}
  return (
    <div style={{display:'flex',height:'100vh',background:'#0a0a0a',fontFamily:'system-ui,sans-serif',overflow:'hidden'}}>
      <div style={{width:'210px',background:'#0f0f0f',borderRight:'1px solid #1a1a1a',display:'flex',flexDirection:'column',padding:'24px 0',flexShrink:0}}>
        <div style={{display:'flex',alignItems:'center',gap:'8px',padding:'0 18px',marginBottom:'28px'}}><div style={{width:'8px',height:'8px',borderRadius:'50%',background:'#6366f1',boxShadow:'0 0 10px #6366f1'}}/><span style={{color:'#fafafa',fontSize:'15px',fontWeight:'600'}}>DevIQ</span></div>
        {nav.map(n=>{const I=n.icon;const a=tab===n.id;return(<button key={n.id} onClick={()=>setTab(n.id)} style={{display:'flex',alignItems:'center',gap:'10px',padding:'9px 18px',background:a?'rgba(99,102,241,0.08)':'none',border:'none',borderLeft:`2px solid ${a?'#6366f1':'transparent'}`,cursor:'pointer',color:a?'#a5b4fc':'#71717a',fontSize:'13px',fontWeight:'500',width:'100%',transition:'all 0.15s',position:'relative'}}><I size={14}/>{n.label}{n.id==='alerts'&&active.length>0&&<span style={{marginLeft:'auto',background:'#ef4444',color:'#fff',fontSize:'10px',fontWeight:'600',padding:'1px 5px',borderRadius:'20px'}}>{active.length}</span>}</button>)})}
        <div style={{marginTop:'auto',padding:'16px 18px',borderTop:'1px solid #1a1a1a'}}>
          <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'10px'}}>
            <div style={{width:'30px',height:'30px',borderRadius:'50%',background:'rgba(99,102,241,0.15)',border:'1px solid #6366f1',display:'flex',alignItems:'center',justifyContent:'center',color:'#a5b4fc',fontSize:'11px',fontWeight:'600'}}>{name.split(' ').map((n:string)=>n[0]).join('').slice(0,2)}</div>
            <div><p style={{color:'#fafafa',fontSize:'12px',fontWeight:'500',margin:0}}>{name}</p><p style={{color:'#52525b',fontSize:'10px',margin:0}}>Manager</p></div>
          </div>
          <button onClick={()=>{localStorage.clear();window.location.href='/login'}} style={{display:'flex',alignItems:'center',gap:'6px',color:'#52525b',background:'none',border:'none',cursor:'pointer',fontSize:'11px',padding:0}}><LogOut size={12}/>Sign out</button>
        </div>
      </div>
      <div style={{flex:1,overflow:'auto',padding:'28px 32px'}}>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'24px'}}>
          <div><h1 style={{color:'#fafafa',fontSize:'21px',fontWeight:'500',letterSpacing:'-0.5px',margin:0}}>Team Dashboard</h1><p style={{color:'#71717a',fontSize:'13px',margin:'4px 0 0'}}>Live scores — updates on every commit</p></div>
          <div style={{display:'flex',alignItems:'center',gap:'6px'}}><div style={{width:'7px',height:'7px',borderRadius:'50%',background:'#22c55e',boxShadow:'0 0 8px #22c55e'}}/><span style={{color:'#52525b',fontSize:'12px'}}>Live</span></div>
        </div>

        {active.length>0&&(
          <div style={{marginBottom:'20px',display:'flex',flexDirection:'column',gap:'8px'}}>
            {active.map(a=>(
              <div key={a.id} style={{display:'flex',alignItems:'center',gap:'12px',background:a.type==='blocker'?'rgba(245,158,11,0.06)':a.type==='burnout'?'rgba(239,68,68,0.06)':'rgba(99,102,241,0.06)',border:`1px solid ${a.type==='blocker'?'rgba(245,158,11,0.2)':a.type==='burnout'?'rgba(239,68,68,0.2)':'rgba(99,102,241,0.2)'}`,borderRadius:'10px',padding:'12px 16px'}}>
                <AlertTriangle size={15} color={a.type==='blocker'?'#f59e0b':a.type==='burnout'?'#ef4444':'#6366f1'}/>
                <div style={{flex:1}}><span style={{color:'#fafafa',fontSize:'12px',fontWeight:'500'}}>{a.dev}</span><span style={{color:'#71717a',fontSize:'12px'}}> — {a.msg}</span></div>
                <button onClick={()=>setDismissed([...dismissed,a.id])} style={{background:'none',border:'none',cursor:'pointer',color:'#52525b',padding:0,display:'flex'}}><X size={14}/></button>
              </div>
            ))}
          </div>
        )}

        {tab==='overview'&&(
          <>
            <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'12px',marginBottom:'20px'}}>
              {[{label:'Team avg score',val:teamAvg,color:'#6366f1'},{label:'At risk',val:DEVS.filter(d=>d.burnout).length,color:'#ef4444'},{label:'Active blockers',val:active.filter(a=>a.type==='blocker').length,color:'#f59e0b'},{label:'High performers',val:DEVS.filter(d=>d.score>=75).length,color:'#22c55e'}].map((m,i)=>(
                <div key={i} style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                  <p style={{color:'#71717a',fontSize:'12px',margin:'0 0 10px'}}>{m.label}</p>
                  <span style={{color:m.color,fontSize:'28px',fontWeight:'700',letterSpacing:'-1px'}}>{m.val}</span>
                </div>
              ))}
            </div>
            <div style={{display:'grid',gridTemplateColumns:'1fr 300px',gap:'14px',marginBottom:'20px'}}>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>Team score trend — 8 weeks</p>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={TREND} margin={{top:5,right:5,bottom:0,left:-20}}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false}/>
                    <XAxis dataKey="week" tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <YAxis domain={[0,100]} tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <Tooltip content={<T2/>}/>
                    <Legend wrapperStyle={{fontSize:'11px',color:'#71717a',paddingTop:'8px'}}/>
                    <Line type="monotone" dataKey="rajan" stroke="#6366f1" strokeWidth={2} dot={false} name="Rajan"/>
                    <Line type="monotone" dataKey="arjun" stroke="#22c55e" strokeWidth={2} dot={false} name="Arjun"/>
                    <Line type="monotone" dataKey="priya" stroke="#ef4444" strokeWidth={2} dot={false} name="Priya" strokeDasharray="4 4"/>
                    <Line type="monotone" dataKey="karan" stroke="#f59e0b" strokeWidth={2} dot={false} name="Karan"/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>Current scores</p>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={BARS} margin={{top:5,right:5,bottom:0,left:-20}} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" horizontal={false}/>
                    <XAxis type="number" domain={[0,100]} tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <YAxis type="category" dataKey="name" tick={{fill:'#a1a1aa',fontSize:11}} tickLine={false} axisLine={false} width={50}/>
                    <Tooltip contentStyle={{background:'#161616',border:'1px solid #262626',borderRadius:'8px',color:'#fafafa',fontSize:'12px'}}/>
                    <Bar dataKey="score" radius={[0,4,4,0]}>{BARS.map((_,i)=><Cell key={i} fill={BAR_COLORS[i%BAR_COLORS.length]}/>)}</Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'12px'}}>
              {DEVS.map((d,i)=>{
                const tc=d.score>=70?'#22c55e':d.score>=40?'#f59e0b':'#ef4444'
                const tr=d.score-d.prev
                return(
                  <div key={i} style={{background:'#111111',border:`1px solid ${d.burnout?'rgba(239,68,68,0.3)':'#1f1f1f'}`,borderRadius:'12px',padding:'18px',transition:'border-color 0.2s'}} onMouseEnter={e=>!d.burnout&&(e.currentTarget.style.borderColor='#2a2a2a')} onMouseLeave={e=>!d.burnout&&(e.currentTarget.style.borderColor='#1f1f1f')}>
                    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'12px'}}>
                      <div style={{display:'flex',alignItems:'center',gap:'8px'}}>
                        <div style={{width:'32px',height:'32px',borderRadius:'50%',background:'rgba(99,102,241,0.15)',border:'1px solid #6366f1',display:'flex',alignItems:'center',justifyContent:'center',color:'#a5b4fc',fontSize:'11px',fontWeight:'600'}}>{d.name.split(' ').map(n=>n[0]).join('')}</div>
                        <div><p style={{color:'#fafafa',fontSize:'12px',fontWeight:'500',margin:0}}>{d.name}</p><p style={{color:'#52525b',fontSize:'10px',margin:0,fontFamily:'monospace'}}>{d.ticket}</p></div>
                      </div>
                      {d.burnout&&<span style={{background:'rgba(239,68,68,0.1)',color:'#f87171',fontSize:'10px',padding:'2px 7px',borderRadius:'20px',fontWeight:'500'}}>At risk</span>}
                    </div>
                    <div style={{display:'flex',alignItems:'baseline',gap:'4px',marginBottom:'8px'}}>
                      <span style={{color:tc,fontSize:'32px',fontWeight:'700',letterSpacing:'-1px',lineHeight:1}}>{d.score}</span>
                      <span style={{color:'#52525b',fontSize:'14px'}}>/100</span>
                      <span style={{color:tr>=0?'#22c55e':'#ef4444',fontSize:'11px',marginLeft:'4px',display:'flex',alignItems:'center',gap:'2px'}}>{tr>=0?<TrendingUp size={11}/>:<TrendingDown size={11}/>}{tr>=0?'+':''}{tr}</span>
                    </div>
                    <div style={{display:'flex',flexDirection:'column',gap:'5px',marginBottom:'10px'}}>
                      {[{l:'Relevance',v:d.relevance,c:'#6366f1'},{l:'Impact',v:d.impact,c:'#22c55e'},{l:'Complexity',v:d.complexity,c:'#f59e0b'},{l:'Glue work',v:d.glue,c:'#8b5cf6'}].map(b=>(
                        <div key={b.l} style={{display:'flex',alignItems:'center',gap:'8px'}}>
                          <span style={{color:'#52525b',fontSize:'10px',width:'65px',flexShrink:0}}>{b.l}</span>
                          <div style={{flex:1,background:'#1a1a1a',borderRadius:'2px',height:'3px'}}><div style={{background:b.c,width:`${b.v*100}%`,height:'100%',borderRadius:'2px'}}/></div>
                          <span style={{color:'#71717a',fontSize:'10px',width:'28px',textAlign:'right',fontFamily:'monospace'}}>{Math.round(b.v*100)}</span>
                        </div>
                      ))}
                    </div>
                    <p style={{color:'#52525b',fontSize:'11px',margin:'0 0 8px',lineHeight:1.5,fontStyle:'italic'}}>"{d.explanation.slice(0,60)}..."</p>
                    <div style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                      <span style={{color:'#3f3f46',fontSize:'10px',fontFamily:'monospace'}}>{d.lastCommit}</span>
                      <span style={{background:'rgba(99,102,241,0.1)',color:'#a5b4fc',fontSize:'10px',padding:'1px 6px',borderRadius:'20px'}}>{d.confidence}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}

        {tab==='match'&&(
          <div style={{maxWidth:'600px'}}>
            <p style={{color:'#fafafa',fontSize:'14px',fontWeight:'500',margin:'0 0 8px'}}>Find best developer for a project</p>
            <p style={{color:'#71717a',fontSize:'13px',margin:'0 0 16px'}}>Describe your project requirements and we'll match the best developer from your team</p>
            <textarea value={matchQ} onChange={e=>setMatchQ(e.target.value)} placeholder="e.g. We need someone to build OAuth integration with payment gateway and mobile API design..." rows={4} style={{width:'100%',background:'#111111',border:'1px solid #1f1f1f',borderRadius:'10px',padding:'12px',color:'#fafafa',fontSize:'13px',outline:'none',resize:'none',fontFamily:'system-ui',marginBottom:'10px'}}/>
            <button onClick={handleMatch} style={{background:'#6366f1',border:'none',borderRadius:'8px',padding:'10px 20px',color:'#fff',fontSize:'13px',fontWeight:'500',cursor:'pointer',marginBottom:'20px'}}>Find best match →</button>
            {matchRes&&(
              <div style={{display:'flex',flexDirection:'column',gap:'10px'}}>
                {matchRes.map((d,i)=>(
                  <div key={i} style={{background:'#111111',border:`1px solid ${i===0?'#6366f1':'#1f1f1f'}`,borderRadius:'10px',padding:'14px 16px',display:'flex',alignItems:'center',gap:'16px'}}>
                    <div style={{width:'28px',height:'28px',borderRadius:'50%',background:i===0?'rgba(99,102,241,0.2)':'rgba(255,255,255,0.05)',border:`1px solid ${i===0?'#6366f1':'#2a2a2a'}`,display:'flex',alignItems:'center',justifyContent:'center',color:i===0?'#a5b4fc':'#52525b',fontSize:'12px',fontWeight:'700',flexShrink:0}}>#{i+1}</div>
                    <div style={{flex:1}}><p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:0}}>{d.name}</p><p style={{color:'#71717a',fontSize:'11px',margin:'2px 0 0'}}>Avg score: {d.score}/100</p></div>
                    <div style={{textAlign:'right'}}><p style={{color:'#22c55e',fontSize:'16px',fontWeight:'700',margin:0}}>{d.match}%</p><p style={{color:'#52525b',fontSize:'10px',margin:0}}>match</p></div>
                    <div style={{width:'60px',background:'#1a1a1a',borderRadius:'3px',height:'4px'}}><div style={{background:'#22c55e',width:`${d.match}%`,height:'100%',borderRadius:'3px'}}/></div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <style>{`*{box-sizing:border-box} ::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:#0f0f0f} ::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:2px}`}</style>
    </div>
  )
}
