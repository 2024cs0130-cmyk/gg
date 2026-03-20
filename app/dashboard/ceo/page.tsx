'use client'
import { useState } from 'react'
import { Building2, Activity, Shield, BarChart2, FileText, LogOut, TrendingUp, TrendingDown, AlertOctagon, Users, Zap } from 'lucide-react'
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, RadarChart, Radar, PolarGrid, PolarAngleAxis, AreaChart, Area } from 'recharts'

const DEVS = [
  {name:'Rajan Kumar',initials:'RK',score:88,burnout:false,risk:'low',module:'payments-service'},
  {name:'Priya Sharma',initials:'PS',score:81,burnout:false,risk:'medium',module:'auth-gateway'},
  {name:'Arjun Malhothra',initials:'AM',score:74,burnout:true,risk:'high',module:'mobile-sync'},
  {name:'Karan Patel',initials:'KP',score:93,burnout:false,risk:'low',module:'search-indexer'},
  {name:'Meera Iyer',initials:'MI',score:86,burnout:false,risk:'low',module:'frontend-shell'},
  {name:'Nisha Verma',initials:'NV',score:69,burnout:true,risk:'high',module:'etl-pipeline'},
]
const WEEKS = [
  {week:'W1',avg:66,burnout:1,blockers:4},
  {week:'W2',avg:69,burnout:1,blockers:4},
  {week:'W3',avg:71,burnout:2,blockers:3},
  {week:'W4',avg:73,burnout:2,blockers:3},
  {week:'W5',avg:76,burnout:3,blockers:2},
  {week:'W6',avg:78,burnout:2,blockers:2},
  {week:'W7',avg:80,burnout:2,blockers:1},
  {week:'W8',avg:82,burnout:2,blockers:1},
]
const SKILL_RADAR = [
  {s:'Auth',team:72,ideal:100},
  {s:'Payments',team:64,ideal:100},
  {s:'Mobile',team:52,ideal:100},
  {s:'ML',team:41,ideal:100},
  {s:'DevOps',team:67,ideal:100},
  {s:'Frontend',team:84,ideal:100},
  {s:'Database',team:77,ideal:100},
]
const KNOWLEDGE_RISKS: Array<{ dev: string; module: string; owns: number; burnout: string; risk: string }> = [
  {dev:'Arjun Malhothra',module:'mobile-sync',owns:78,burnout:'high',risk:'critical'},
  {dev:'Nisha Verma',module:'etl-pipeline',owns:72,burnout:'high',risk:'high'},
  {dev:'Priya Sharma',module:'auth-gateway',owns:64,burnout:'medium',risk:'medium'},
  {dev:'Karan Patel',module:'search-indexer',owns:58,burnout:'low',risk:'low'},
]
const TOP3: Array<{ name: string; score: number; achievement: string; medal: string }> = [
  {name:'Karan Patel',score:93,achievement:'Reduced API latency by 38%',medal:'🥇'},
  {name:'Rajan Kumar',score:88,achievement:'Shipped payment retry engine',medal:'🥈'},
  {name:'Meera Iyer',score:86,achievement:'Cut frontend bundle size by 26%',medal:'🥉'},
]
const teamAvg = Math.round(DEVS.reduce((a,b)=>a+b.score,0)/DEVS.length)
const T3 = ({active,payload,label}:any)=>active&&payload?.length?<div style={{background:'#161616',border:'1px solid #262626',borderRadius:'8px',padding:'10px 12px'}}><p style={{color:'#a1a1aa',fontSize:'11px',margin:'0 0 6px'}}>{label}</p>{payload.map((p:any,i:number)=><p key={i} style={{color:p.color||'#fafafa',fontSize:'12px',margin:'2px 0'}}>{p.name}: {typeof p.value==='number'?p.value.toFixed(1):p.value}</p>)}</div>:null

export default function CEODash() {
  const [tab,setTab]=useState('health')
  const [downloading,setDownloading]=useState(false)
  const name=typeof window!=='undefined'?localStorage.getItem('display_name')||'CEO':'CEO'
  const handleReport=async()=>{setDownloading(true);await new Promise(r=>setTimeout(r,2000));setDownloading(false);alert('Report ready — connect to GET /ceo/org/report endpoint')}
  const nav=[{icon:Activity,label:'Org Health',id:'health'},{icon:Shield,label:'Risk Radar',id:'risk'},{icon:BarChart2,label:'Skill Gaps',id:'skills'},{icon:FileText,label:'Reports',id:'reports'}]
  const riskColor=(r:string)=>r==='critical'?'#ef4444':r==='high'?'#f59e0b':r==='medium'?'#6366f1':'#22c55e'
  return (
    <div style={{display:'flex',height:'100vh',background:'#0a0a0a',fontFamily:'system-ui,sans-serif',overflow:'hidden'}}>
      <div style={{width:'210px',background:'#0f0f0f',borderRight:'1px solid #1a1a1a',display:'flex',flexDirection:'column',padding:'24px 0',flexShrink:0}}>
        <div style={{display:'flex',alignItems:'center',gap:'8px',padding:'0 18px',marginBottom:'28px'}}><div style={{width:'8px',height:'8px',borderRadius:'50%',background:'#6366f1',boxShadow:'0 0 10px #6366f1'}}/><span style={{color:'#fafafa',fontSize:'15px',fontWeight:'600'}}>DevIQ</span></div>
        {nav.map(n=>{const I=n.icon;const a=tab===n.id;return(<button key={n.id} onClick={()=>setTab(n.id)} style={{display:'flex',alignItems:'center',gap:'10px',padding:'9px 18px',background:a?'rgba(99,102,241,0.08)':'none',border:'none',borderLeft:`2px solid ${a?'#6366f1':'transparent'}`,cursor:'pointer',color:a?'#a5b4fc':'#71717a',fontSize:'13px',fontWeight:'500',width:'100%',transition:'all 0.15s'}}><I size={14}/>{n.label}</button>)})}
        <div style={{marginTop:'auto',padding:'16px 18px',borderTop:'1px solid #1a1a1a'}}>
          <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'10px'}}>
            <div style={{width:'30px',height:'30px',borderRadius:'50%',background:'rgba(245,158,11,0.15)',border:'1px solid #f59e0b',display:'flex',alignItems:'center',justifyContent:'center',color:'#fcd34d',fontSize:'11px',fontWeight:'600'}}>{name.split(' ').map((n:string)=>n[0]).join('').slice(0,2)}</div>
            <div><p style={{color:'#fafafa',fontSize:'12px',fontWeight:'500',margin:0}}>{name}</p><p style={{color:'#52525b',fontSize:'10px',margin:0}}>CEO</p></div>
          </div>
          <button onClick={()=>{localStorage.clear();window.location.href='/login'}} style={{display:'flex',alignItems:'center',gap:'6px',color:'#52525b',background:'none',border:'none',cursor:'pointer',fontSize:'11px',padding:0}}><LogOut size={12}/>Sign out</button>
        </div>
      </div>

      <div style={{flex:1,overflow:'auto',padding:'28px 32px'}}>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'24px'}}>
          <div><h1 style={{color:'#fafafa',fontSize:'21px',fontWeight:'500',letterSpacing:'-0.5px',margin:0}}>Organisation Intelligence</h1><p style={{color:'#71717a',fontSize:'13px',margin:'4px 0 0'}}>Real-time engineering health for Test Company</p></div>
          <button onClick={handleReport} style={{display:'flex',alignItems:'center',gap:'8px',background:'rgba(99,102,241,0.1)',border:'1px solid rgba(99,102,241,0.3)',borderRadius:'8px',padding:'8px 16px',color:'#a5b4fc',fontSize:'12px',fontWeight:'500',cursor:'pointer'}}>
            {downloading?<div style={{width:'12px',height:'12px',border:'2px solid rgba(165,180,252,0.3)',borderTopColor:'#a5b4fc',borderRadius:'50%',animation:'spin 0.7s linear infinite'}}/>:<FileText size={13}/>}
            {downloading?'Generating...':'Download PDF report'}
          </button>
        </div>

        {tab==='health'&&(
          <>
            <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:'12px',marginBottom:'20px'}}>
              {[{label:'Team health',val:`${teamAvg}%`,color:'#6366f1',Icon:Activity},{label:'Team size',val:DEVS.length,color:'#a1a1aa',Icon:Users},{label:'At burnout risk',val:DEVS.filter(d=>d.burnout).length,color:'#ef4444',Icon:AlertOctagon},{label:'Knowledge risks',val:KNOWLEDGE_RISKS.filter(r=>r.risk==='critical').length,color:'#f59e0b',Icon:Shield},{label:'Top score',val:Math.max(...DEVS.map(d=>d.score)),color:'#22c55e',Icon:Zap}].map((m,i)=>(
                <div key={i} style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'16px'}}>
                  <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'10px'}}><span style={{color:'#71717a',fontSize:'11px'}}>{m.label}</span><m.Icon size={13} color="#3f3f46"/></div>
                  <span style={{color:m.color,fontSize:'26px',fontWeight:'700',letterSpacing:'-1px'}}>{m.val}</span>
                </div>
              ))}
            </div>

            <div style={{display:'grid',gridTemplateColumns:'1fr 280px',gap:'14px',marginBottom:'20px'}}>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>8-week trend — team avg + burnout risk</p>
                <ResponsiveContainer width="100%" height={200}>
                  <ComposedChart data={WEEKS} margin={{top:5,right:5,bottom:0,left:-20}}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false}/>
                    <XAxis dataKey="week" tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <YAxis yAxisId="left" domain={[0,100]} tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <YAxis yAxisId="right" orientation="right" domain={[0,5]} tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <Tooltip content={<T3/>}/>
                    <Legend wrapperStyle={{fontSize:'11px',color:'#71717a',paddingTop:'8px'}}/>
                    <Bar yAxisId="left" dataKey="avg" fill="#6366f1" fillOpacity={0.6} radius={[3,3,0,0]} name="Team avg"/>
                    <Line yAxisId="right" type="monotone" dataKey="burnout" stroke="#ef4444" strokeWidth={2} dot={false} name="Burnout risk"/>
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 12px'}}>Top performers</p>
                <div style={{display:'flex',flexDirection:'column',gap:'10px'}}>
                  {TOP3.map((t,i)=>(
                    <div key={i} style={{display:'flex',alignItems:'center',gap:'10px',background:'#161616',borderRadius:'8px',padding:'10px 12px',border:'1px solid #1a1a1a'}}>
                      <span style={{fontSize:'18px'}}>{t.medal}</span>
                      <div style={{flex:1}}><p style={{color:'#fafafa',fontSize:'12px',fontWeight:'500',margin:0}}>{t.name}</p><p style={{color:'#52525b',fontSize:'10px',margin:'2px 0 0'}}>{t.achievement}</p></div>
                      <span style={{color:'#22c55e',fontSize:'14px',fontWeight:'700',fontFamily:'monospace'}}>{t.score}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
              <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>Developer performance heatmap</p>
              <div style={{display:'grid',gridTemplateColumns:'repeat(6,1fr)',gap:'8px'}}>
                {DEVS.map((d,i)=>{
                  const intensity=d.score/100
                  const bg=d.score>=70?`rgba(99,102,241,${0.1+intensity*0.4})`:d.score>=40?`rgba(245,158,11,${0.1+intensity*0.3})`:`rgba(239,68,68,${0.1+intensity*0.3})`
                  const border=d.score>=70?`rgba(99,102,241,${0.3+intensity*0.4})`:d.score>=40?`rgba(245,158,11,0.4)`:`rgba(239,68,68,0.4)`
                  return(
                    <div key={i} style={{background:bg,border:`1px solid ${border}`,borderRadius:'10px',padding:'14px 10px',textAlign:'center'}}>
                      <div style={{width:'32px',height:'32px',borderRadius:'50%',background:'rgba(0,0,0,0.3)',display:'flex',alignItems:'center',justifyContent:'center',color:'#fafafa',fontSize:'11px',fontWeight:'600',margin:'0 auto 8px'}}>{d.initials}</div>
                      <p style={{color:'#fafafa',fontSize:'11px',fontWeight:'500',margin:'0 0 4px'}}>{d.name.split(' ')[0]}</p>
                      <p style={{color:'#fafafa',fontSize:'20px',fontWeight:'700',margin:'0 0 4px',letterSpacing:'-1px'}}>{d.score}</p>
                      {d.burnout&&<span style={{background:'rgba(239,68,68,0.2)',color:'#f87171',fontSize:'9px',padding:'1px 5px',borderRadius:'20px'}}>At risk</span>}
                    </div>
                  )
                })}
              </div>
            </div>
          </>
        )}

        {tab==='risk'&&(
          <>
            <p style={{color:'#fafafa',fontSize:'14px',fontWeight:'500',margin:'0 0 16px'}}>Knowledge concentration risk</p>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'14px',marginBottom:'20px'}}>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',overflow:'hidden'}}>
                <div style={{padding:'14px 18px',borderBottom:'1px solid #1a1a1a'}}><p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:0}}>Risk registry</p></div>
                <table style={{width:'100%',borderCollapse:'collapse'}}>
                  <thead><tr style={{borderBottom:'1px solid #1a1a1a'}}>{['Developer','Module','Owns %','Burnout','Risk'].map(h=><th key={h} style={{padding:'9px 16px',color:'#52525b',fontSize:'11px',fontWeight:'500',textAlign:'left'}}>{h}</th>)}</tr></thead>
                  <tbody>{KNOWLEDGE_RISKS.map((r,i)=>(
                    <tr key={i} style={{borderBottom:'1px solid #141414'}}>
                      <td style={{padding:'10px 16px',color:'#fafafa',fontSize:'12px'}}>{r.dev}</td>
                      <td style={{padding:'10px 16px',color:'#71717a',fontSize:'12px',fontFamily:'monospace'}}>{r.module}</td>
                      <td style={{padding:'10px 16px'}}><div style={{display:'flex',alignItems:'center',gap:'6px'}}><div style={{flex:1,background:'#1a1a1a',borderRadius:'2px',height:'4px',maxWidth:'60px'}}><div style={{background:'#6366f1',width:`${r.owns}%`,height:'100%',borderRadius:'2px'}}/></div><span style={{color:'#71717a',fontSize:'11px'}}>{r.owns}%</span></div></td>
                      <td style={{padding:'10px 16px'}}><span style={{color:riskColor(r.burnout),fontSize:'11px'}}>{r.burnout}</span></td>
                      <td style={{padding:'10px 16px'}}><span style={{background:`${riskColor(r.risk)}18`,color:riskColor(r.risk),fontSize:'11px',padding:'2px 8px',borderRadius:'20px',fontWeight:'500'}}>{r.risk}</span></td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>Score vs burnout risk</p>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={WEEKS} margin={{top:5,right:5,bottom:0,left:-20}}>
                    <defs><linearGradient id="rg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.15}/><stop offset="95%" stopColor="#ef4444" stopOpacity={0}/></linearGradient></defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false}/>
                    <XAxis dataKey="week" tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <YAxis tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                    <Tooltip contentStyle={{background:'#161616',border:'1px solid #262626',borderRadius:'8px',color:'#fafafa',fontSize:'12px'}}/>
                    <Area type="monotone" dataKey="burnout" stroke="#ef4444" strokeWidth={2} fill="url(#rg)" name="Burnout risk"/>
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}

        {tab==='skills'&&(
          <>
            <p style={{color:'#fafafa',fontSize:'14px',fontWeight:'500',margin:'0 0 6px'}}>Team skill gap analysis</p>
            <p style={{color:'#71717a',fontSize:'13px',margin:'0 0 20px'}}>Current team coverage vs ideal across all domains</p>
            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'14px'}}>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 8px'}}>Skill radar</p>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={SKILL_RADAR}>
                    <PolarGrid stroke="#1f1f1f"/>
                    <PolarAngleAxis dataKey="s" tick={{fill:'#71717a',fontSize:11}}/>
                    <Radar dataKey="ideal" stroke="#1f1f1f" fill="#1f1f1f" fillOpacity={0.3} name="Ideal"/>
                    <Radar dataKey="team" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} name="Team"/>
                    <Legend wrapperStyle={{fontSize:'11px',color:'#71717a'}}/>
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 16px'}}>Gap analysis</p>
                <div style={{display:'flex',flexDirection:'column',gap:'10px'}}>
                  {SKILL_RADAR.map((s,i)=>{const gap=s.ideal-s.team;return(
                    <div key={i}>
                      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'4px'}}>
                        <span style={{color:'#a1a1aa',fontSize:'12px'}}>{s.s}</span>
                        <span style={{color:gap>50?'#ef4444':gap>30?'#f59e0b':'#22c55e',fontSize:'11px',fontWeight:'500'}}>{gap>50?'Critical gap':gap>30?'Needs hiring':'Good coverage'}</span>
                      </div>
                      <div style={{background:'#1a1a1a',borderRadius:'3px',height:'5px',overflow:'hidden'}}>
                        <div style={{background:gap>50?'#ef4444':gap>30?'#f59e0b':'#22c55e',width:`${s.team}%`,height:'100%',borderRadius:'3px',transition:'width 0.5s'}}/>
                      </div>
                    </div>
                  )})}
                </div>
                <div style={{marginTop:'16px',background:'rgba(239,68,68,0.06)',border:'1px solid rgba(239,68,68,0.15)',borderRadius:'8px',padding:'10px 14px'}}>
                  <p style={{color:'#f87171',fontSize:'12px',fontWeight:'500',margin:'0 0 4px'}}>Hiring recommendation</p>
                  <p style={{color:'#71717a',fontSize:'11px',margin:0}}>Consider hiring ML engineer and Mobile developer — both have critical gaps that will block upcoming projects.</p>
                </div>
              </div>
            </div>
          </>
        )}

        {tab==='reports'&&(
          <div style={{maxWidth:'500px'}}>
            <p style={{color:'#fafafa',fontSize:'14px',fontWeight:'500',margin:'0 0 6px'}}>PDF Reports</p>
            <p style={{color:'#71717a',fontSize:'13px',margin:'0 0 20px'}}>Generate and download comprehensive team reports</p>
            {[{title:'Weekly team report',desc:'Team health, top performers, risk alerts, skill gaps',type:'weekly'},{title:'Monthly summary',desc:'Month-over-month trends, hiring recommendations',type:'monthly'},{title:'Risk assessment',desc:'Knowledge concentration, burnout risks, bus factors',type:'risk'}].map((r,i)=>(
              <div key={i} style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'10px',padding:'16px',marginBottom:'10px',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                <div><p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:0}}>{r.title}</p><p style={{color:'#71717a',fontSize:'11px',margin:'4px 0 0'}}>{r.desc}</p></div>
                <button onClick={handleReport} style={{background:'rgba(99,102,241,0.1)',border:'1px solid rgba(99,102,241,0.3)',borderRadius:'7px',padding:'7px 14px',color:'#a5b4fc',fontSize:'12px',fontWeight:'500',cursor:'pointer',whiteSpace:'nowrap'}}>{downloading?'Generating...':'Download PDF'}</button>
              </div>
            ))}
          </div>
        )}
      </div>
      <style>{`*{box-sizing:border-box} @keyframes spin{to{transform:rotate(360deg)}} ::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:#0f0f0f} ::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:2px}`}</style>
    </div>
  )
}
