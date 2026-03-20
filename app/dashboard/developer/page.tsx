'use client'
import { useEffect, useState } from 'react'
import { TrendingUp, Trophy, User, LogOut, Zap, GitCommit, MessageSquare, Eye, EyeOff } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, BarChart, Bar } from 'recharts'

const radarData = [{s:'Relevance',v:82},{s:'Impact',v:74},{s:'Complexity',v:91},{s:'Glue Work',v:68},{s:'Consistency',v:79},{s:'Coverage',v:85}]
const achievements: Array<{ title: string; desc: string; color: string; icon: string }> = []
const buildMockScores = () =>
  Array.from({ length: 0 }, () => ({
    sha: '',
    score: 0,
    ticket: '',
    confidence: 'low',
    explanation: '',
    created_at: '',
  }))

const buildWeekData = () =>
  ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => ({
    day: d,
    score: 0,
  }))
const S = ({s}:{s:number})=>{const c=s>=70?'#22c55e':s>=40?'#f59e0b':'#ef4444';return <span style={{background:`${c}18`,color:c,fontSize:'11px',fontWeight:'600',padding:'2px 8px',borderRadius:'20px',fontFamily:'monospace'}}>{s}</span>}
const T = ({active,payload}:any)=>active&&payload?.length?<div style={{background:'#161616',border:'1px solid #262626',borderRadius:'8px',padding:'8px 12px'}}><p style={{color:'#6366f1',fontSize:'16px',fontWeight:'700',margin:0}}>{payload[0].value}<span style={{color:'#52525b',fontSize:'11px'}}>/100</span></p></div>:null

export default function DevDash() {
  const [tab,setTab]=useState('scores')
  const [ctx,setCtx]=useState<string|null>(null)
  const [name, setName] = useState('Developer')
  const [scores, setScores] = useState<Array<{ sha: string; score: number; ticket: string; confidence: string; explanation: string; created_at: string }>>([])
  const [weekData, setWeekData] = useState<Array<{ day: string; score: number }>>([])

  useEffect(() => {
    setName(localStorage.getItem('display_name') || 'Developer')
    setScores(buildMockScores())
    setWeekData(buildWeekData())
  }, [])

  const latest=scores[0]?.score||0
  const wSlice = scores.slice(0, 7)
  const pSlice = scores.slice(7, 14)
  const wavg = wSlice.length ? Math.round(wSlice.reduce((a,b)=>a+b.score,0)/wSlice.length) : 0
  const pavg = pSlice.length ? Math.round(pSlice.reduce((a,b)=>a+b.score,0)/pSlice.length) : 0
  const trend=wavg-pavg
  const nav=[{icon:TrendingUp,label:'My Scores',id:'scores'},{icon:Trophy,label:'Achievements',id:'achievements'},{icon:User,label:'Profile',id:'profile'}]
  const achievementTypeColors: Record<string, string> = {
    streak: '#6366f1',
    complexity: '#22c55e',
    teamwork: '#f59e0b',
    milestone: '#a855f7',
  }
  const earnedAchievements: Array<{ icon: string; title: string; description: string; earnedAt: string; type: string }> = []
  const lockedAchievements: Array<{ icon: string; title: string; description: string; progress: number }> = []
  const initials = name.split(' ').map((n:string)=>n[0]).join('').slice(0,2).toUpperCase()
  const totalCommits = scores.length
  const avgScore = scores.length ? Math.round(scores.reduce((a,b)=>a+b.score,0)/scores.length) : 0
  const bestScore = scores.length ? Math.max(...scores.map((s)=>s.score)) : 0
  const prsReviewed = 0
  const bestWeek = weekData.length ? weekData.reduce((best, cur)=> cur.score > best.score ? cur : best, weekData[0]) : { day: '-', score: 0 }
  const worstWeek = weekData.length ? weekData.reduce((worst, cur)=> cur.score < worst.score ? cur : worst, weekData[0]) : { day: '-', score: 0 }
  const domainTagMap: Record<string, string> = {
    Relevance: 'API Design',
    Impact: 'Backend',
    Complexity: 'Auth',
    'Glue Work': 'Collaboration',
    Consistency: 'Testing',
    Coverage: 'Reliability',
  }
  const skillTags = [...radarData].sort((a,b)=>b.v-a.v).slice(0,4).map((d)=>domainTagMap[d.s] || d.s)
  const managerSpecialtyNote = 'No manager notes yet.'
  return (
    <div style={{display:'flex',height:'100vh',background:'#0a0a0a',fontFamily:'system-ui,sans-serif',overflow:'hidden'}}>
      <div style={{width:'210px',background:'#0f0f0f',borderRight:'1px solid #1a1a1a',display:'flex',flexDirection:'column',padding:'24px 0',flexShrink:0}}>
        <div style={{display:'flex',alignItems:'center',gap:'8px',padding:'0 18px',marginBottom:'28px'}}>
          <div style={{width:'8px',height:'8px',borderRadius:'50%',background:'#6366f1',boxShadow:'0 0 10px #6366f1'}}/>
          <span style={{color:'#fafafa',fontSize:'15px',fontWeight:'600'}}>DevIQ</span>
        </div>
        {nav.map(n=>{const I=n.icon;const a=tab===n.id;return(<button key={n.id} onClick={()=>setTab(n.id)} style={{display:'flex',alignItems:'center',gap:'10px',padding:'9px 18px',background:a?'rgba(99,102,241,0.08)':'none',border:'none',borderLeft:`2px solid ${a?'#6366f1':'transparent'}`,cursor:'pointer',color:a?'#a5b4fc':'#71717a',fontSize:'13px',fontWeight:'500',width:'100%',transition:'all 0.15s'}}><I size={14}/>{n.label}</button>)})}
        <div style={{marginTop:'auto',padding:'16px 18px',borderTop:'1px solid #1a1a1a'}}>
          <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'10px'}}>
            <div style={{width:'30px',height:'30px',borderRadius:'50%',background:'rgba(99,102,241,0.15)',border:'1px solid #6366f1',display:'flex',alignItems:'center',justifyContent:'center',color:'#a5b4fc',fontSize:'11px',fontWeight:'600'}}>{name.split(' ').map((n:string)=>n[0]).join('').slice(0,2)}</div>
            <div><p style={{color:'#fafafa',fontSize:'12px',fontWeight:'500',margin:0}}>{name}</p><p style={{color:'#52525b',fontSize:'10px',margin:0}}>Developer</p></div>
          </div>
          <button onClick={()=>{localStorage.clear();window.location.href='/login'}} style={{display:'flex',alignItems:'center',gap:'6px',color:'#52525b',background:'none',border:'none',cursor:'pointer',fontSize:'11px',padding:0}}><LogOut size={12}/>Sign out</button>
        </div>
      </div>
      <div style={{flex:1,overflow:'auto',padding:'28px 32px'}}>
        {tab === 'scores' && (
          <>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'24px'}}>
          <div><h1 style={{color:'#fafafa',fontSize:'21px',fontWeight:'500',letterSpacing:'-0.5px',margin:0}}>Good work, {name.split(' ')[0]}</h1><p style={{color:'#71717a',fontSize:'13px',margin:'4px 0 0'}}>Your effort scores - updated on every commit</p></div>
          <div style={{display:'flex',alignItems:'center',gap:'6px'}}><div style={{width:'7px',height:'7px',borderRadius:'50%',background:'#22c55e',boxShadow:'0 0 8px #22c55e'}}/><span style={{color:'#52525b',fontSize:'12px'}}>Live</span></div>
        </div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'12px',marginBottom:'20px'}}>
          {[{label:'Latest score',val:latest,unit:'/100',color:latest>=70?'#22c55e':'#f59e0b',Icon:Zap},{label:'Week average',val:wavg,unit:'/100',color:'#6366f1',sub:`${trend>=0?'+':''}${trend} vs last week`,subC:trend>=0?'#22c55e':'#ef4444',Icon:TrendingUp},{label:'Commits today',val:3,unit:' commits',color:'#a1a1aa',Icon:GitCommit},{label:'PR reviews',val:6,unit:' this week',color:'#f59e0b',Icon:MessageSquare}].map((m,i)=>(
            <div key={i} style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
              <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'10px'}}><span style={{color:'#71717a',fontSize:'12px'}}>{m.label}</span><m.Icon size={13} color="#3f3f46"/></div>
              <div style={{display:'flex',alignItems:'baseline',gap:'2px'}}><span style={{color:m.color,fontSize:'26px',fontWeight:'700',letterSpacing:'-1px',lineHeight:1}}>{m.val}</span><span style={{color:'#52525b',fontSize:'12px'}}>{m.unit}</span></div>
              {m.sub&&<p style={{color:m.subC,fontSize:'11px',margin:'5px 0 0'}}>{m.sub}</p>}
            </div>
          ))}
        </div>
        <div style={{display:'grid',gridTemplateColumns:'1fr 300px',gap:'14px',marginBottom:'20px'}}>
          <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
            <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>Effort score - last 30 commits</p>
            <ResponsiveContainer width="100%" height={190}>
              <AreaChart data={[...scores].reverse()} margin={{top:5,right:5,bottom:0,left:-20}}>
                <defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#6366f1" stopOpacity={0.15}/><stop offset="95%" stopColor="#6366f1" stopOpacity={0}/></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false}/>
                <XAxis dataKey="sha" tick={{fill:'#52525b',fontSize:9,fontFamily:'monospace'}} tickLine={false} axisLine={false} interval={5}/>
                <YAxis domain={[0,100]} tick={{fill:'#52525b',fontSize:9}} tickLine={false} axisLine={false}/>
                <Tooltip content={<T/>}/>
                <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} fill="url(#g1)" dot={false} activeDot={{r:4,fill:'#6366f1'}}/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
            <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 4px'}}>Coding DNA</p>
            <p style={{color:'#52525b',fontSize:'11px',margin:'0 0 4px'}}>Your skill fingerprint</p>
            <ResponsiveContainer width="100%" height={190}>
              <RadarChart data={radarData}><PolarGrid stroke="#1f1f1f"/><PolarAngleAxis dataKey="s" tick={{fill:'#71717a',fontSize:10}}/><Radar dataKey="v" stroke="#6366f1" fill="#6366f1" fillOpacity={0.12} strokeWidth={1.5}/></RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'14px',marginBottom:'20px'}}>
          <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
            <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 14px'}}>This week by day</p>
            <ResponsiveContainer width="100%" height={130}>
              <BarChart data={weekData} margin={{top:0,right:0,bottom:0,left:-20}}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false}/>
                <XAxis dataKey="day" tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                <YAxis domain={[0,100]} tick={{fill:'#52525b',fontSize:10}} tickLine={false} axisLine={false}/>
                <Tooltip contentStyle={{background:'#161616',border:'1px solid #262626',borderRadius:'8px',color:'#fafafa',fontSize:'12px'}}/>
                <Bar dataKey="score" fill="#6366f1" radius={[4,4,0,0]} fillOpacity={0.8}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
            <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:'0 0 12px'}}>This week's wins</p>
            <div style={{display:'flex',flexDirection:'column',gap:'8px'}}>
              {achievements.map((a,i)=>(
                <div key={i} style={{background:'#161616',border:'1px solid #1a1a1a',borderLeft:`3px solid ${a.color}`,borderRadius:'8px',padding:'10px 12px',display:'flex',alignItems:'center',gap:'10px'}}>
                  <span style={{fontSize:'16px'}}>{a.icon}</span>
                  <div><p style={{color:'#fafafa',fontSize:'12px',fontWeight:'500',margin:0}}>{a.title}</p><p style={{color:'#71717a',fontSize:'11px',margin:'2px 0 0'}}>{a.desc}</p></div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',overflow:'hidden'}}>
          <div style={{padding:'14px 18px',borderBottom:'1px solid #1a1a1a',display:'flex',alignItems:'center',justifyContent:'space-between'}}>
            <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'500',margin:0}}>Recent commits</p>
            <span style={{background:'rgba(99,102,241,0.1)',color:'#a5b4fc',fontSize:'11px',padding:'2px 8px',borderRadius:'20px'}}>{scores.length}</span>
          </div>
          <div style={{overflowX:'auto'}}>
            <table style={{width:'100%',borderCollapse:'collapse',minWidth:'700px'}}>
              <thead><tr style={{borderBottom:'1px solid #1a1a1a'}}>{['Commit','Ticket','Score','Confidence','Explanation','Action'].map(h=><th key={h} style={{padding:'9px 16px',color:'#52525b',fontSize:'11px',fontWeight:'500',textAlign:'left',whiteSpace:'nowrap'}}>{h}</th>)}</tr></thead>
              <tbody>
                {scores.slice(0,8).map((s,i)=>(
                  <tr key={i} style={{borderBottom:'1px solid #141414'}} onMouseEnter={e=>(e.currentTarget.style.background='#141414')} onMouseLeave={e=>(e.currentTarget.style.background='transparent')}>
                    <td style={{padding:'9px 16px',color:'#71717a',fontSize:'11px',fontFamily:'monospace'}}>{s.sha}</td>
                    <td style={{padding:'9px 16px'}}><span style={{color:'#6366f1',fontSize:'11px',fontFamily:'monospace'}}>{s.ticket}</span></td>
                    <td style={{padding:'9px 16px'}}><S s={s.score}/></td>
                    <td style={{padding:'9px 16px'}}><span style={{display:'inline-block',width:'7px',height:'7px',borderRadius:'50%',background:s.confidence==='high'?'#22c55e':s.confidence==='medium'?'#f59e0b':'#ef4444'}}/></td>
                    <td style={{padding:'9px 16px',color:'#71717a',fontSize:'11px',maxWidth:'220px'}}><span title={s.explanation}>{s.explanation.slice(0,50)}...</span></td>
                    <td style={{padding:'9px 16px'}}>
                      {ctx===s.sha?<div style={{display:'flex',gap:'4px'}}><input placeholder="Add context..." style={{background:'#1a1a1a',border:'1px solid #2a2a2a',borderRadius:'4px',padding:'3px 7px',color:'#fafafa',fontSize:'11px',outline:'none',width:'120px'}}/><button onClick={()=>setCtx(null)} style={{background:'#6366f1',border:'none',borderRadius:'4px',padding:'3px 7px',color:'#fff',fontSize:'11px',cursor:'pointer'}}>Save</button></div>:<button onClick={()=>setCtx(s.sha)} style={{background:'none',border:'1px solid #262626',borderRadius:'4px',padding:'3px 8px',color:'#71717a',fontSize:'11px',cursor:'pointer'}}>+ Context</button>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
          </>
        )}

        {tab === 'achievements' && (
          <>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'20px'}}>
              <h1 style={{color:'#fafafa',fontSize:'22px',fontWeight:'600',margin:0}}>Your achievements</h1>
              <span style={{background:'rgba(99,102,241,0.12)',border:'1px solid rgba(99,102,241,0.25)',color:'#a5b4fc',fontSize:'12px',padding:'4px 10px',borderRadius:'20px'}}>{earnedAchievements.length} total</span>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'14px',marginBottom:'24px'}}>
              {earnedAchievements.map((a, i)=>(
                <div key={i} style={{background:'#111111',border:`1px solid ${achievementTypeColors[a.type]}`,borderLeft:`3px solid ${achievementTypeColors[a.type]}`,borderRadius:'12px',padding:'14px'}}>
                  <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'8px'}}>
                    <span style={{fontSize:'18px'}}>{a.icon}</span>
                    <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'600',margin:0}}>{a.title}</p>
                  </div>
                  <p style={{color:'#71717a',fontSize:'12px',margin:'0 0 10px'}}>{a.description}</p>
                  <p style={{color:'#52525b',fontSize:'11px',margin:0,fontFamily:'monospace'}}>Earned: {a.earnedAt}</p>
                </div>
              ))}
            </div>

            <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'16px'}}>
              <h3 style={{color:'#fafafa',fontSize:'14px',fontWeight:'600',margin:'0 0 12px'}}>Locked achievements</h3>
              <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'12px'}}>
                {lockedAchievements.map((a, i)=>(
                  <div key={i} style={{background:'#161616',border:'1px solid #2a2a2a',borderRadius:'10px',padding:'12px',opacity:0.72}}>
                    <div style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'8px'}}>
                      <span style={{fontSize:'16px',filter:'grayscale(1)'}}>{a.icon}</span>
                      <p style={{color:'#a1a1aa',fontSize:'12px',fontWeight:'600',margin:0}}>{a.title}</p>
                    </div>
                    <p style={{color:'#71717a',fontSize:'11px',margin:'0 0 8px'}}>{a.description}</p>
                    <div style={{background:'#1f1f1f',height:'6px',borderRadius:'999px',overflow:'hidden',marginBottom:'6px'}}>
                      <div style={{background:'#6366f1',width:`${a.progress}%`,height:'100%'}} />
                    </div>
                    <p style={{color:'#52525b',fontSize:'10px',margin:0,fontFamily:'monospace'}}>{a.progress}% complete</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {tab === 'profile' && (
          <>
            <div style={{display:'grid',gridTemplateColumns:'360px 1fr',gap:'14px',marginBottom:'16px'}}>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <div style={{display:'flex',alignItems:'center',gap:'14px',marginBottom:'12px'}}>
                  <div style={{width:'80px',height:'80px',borderRadius:'50%',background:'rgba(99,102,241,0.14)',border:'1px solid #6366f1',display:'flex',alignItems:'center',justifyContent:'center',color:'#a5b4fc',fontSize:'26px',fontWeight:'700'}}>{initials}</div>
                  <div>
                    <p style={{color:'#fafafa',fontSize:'18px',fontWeight:'600',margin:'0 0 6px'}}>{name}</p>
                    <span style={{background:'rgba(99,102,241,0.12)',color:'#a5b4fc',border:'1px solid rgba(99,102,241,0.25)',borderRadius:'999px',fontSize:'11px',padding:'2px 8px'}}>Developer</span>
                    <p style={{color:'#71717a',fontSize:'12px',margin:'8px 0 0',fontFamily:'monospace'}}>github: {name.toLowerCase().replace(/\s+/g,'')}</p>
                    <p style={{color:'#52525b',fontSize:'11px',margin:'4px 0 0'}}>Member since: Jan 2025</p>
                  </div>
                </div>
              </div>

              <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:'12px'}}>
                {[{k:'Total commits',v:totalCommits},{k:'Avg score',v:avgScore},{k:'Best score',v:bestScore},{k:'PRs reviewed',v:prsReviewed}].map((s, i)=>(
                  <div key={i} style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'16px'}}>
                    <p style={{color:'#71717a',fontSize:'11px',margin:'0 0 8px'}}>{s.k}</p>
                    <p style={{color:'#fafafa',fontSize:'24px',fontWeight:'700',letterSpacing:'-1px',margin:0}}>{s.v}</p>
                  </div>
                ))}
              </div>
            </div>

            <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'14px',marginBottom:'16px'}}>
              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'600',margin:'0 0 8px'}}>Coding DNA</p>
                <ResponsiveContainer width="100%" height={220}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#1f1f1f" />
                    <PolarAngleAxis dataKey="s" tick={{fill:'#71717a',fontSize:11}} />
                    <Radar dataKey="v" stroke="#6366f1" fill="#6366f1" fillOpacity={0.12} strokeWidth={1.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'18px'}}>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'600',margin:'0 0 10px'}}>Skill tags</p>
                <div style={{display:'flex',flexWrap:'wrap',gap:'8px',marginBottom:'14px'}}>
                  {skillTags.map((tag, i)=>(
                    <span key={i} style={{background:'rgba(99,102,241,0.1)',border:'1px solid rgba(99,102,241,0.24)',color:'#a5b4fc',fontSize:'11px',padding:'4px 8px',borderRadius:'999px'}}>{tag}</span>
                  ))}
                </div>
                <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'600',margin:'0 0 8px'}}>Score history summary</p>
                <p style={{color:'#71717a',fontSize:'12px',margin:'0 0 5px'}}>Best week: <span style={{color:'#22c55e'}}>{bestWeek.day} ({bestWeek.score})</span></p>
                <p style={{color:'#71717a',fontSize:'12px',margin:'0 0 5px'}}>Worst week: <span style={{color:'#ef4444'}}>{worstWeek.day} ({worstWeek.score})</span></p>
                <p style={{color:'#71717a',fontSize:'12px',margin:0}}>Improvement trend: <span style={{color:trend >= 0 ? '#22c55e' : '#ef4444'}}>{trend >= 0 ? `+${trend}` : trend} vs previous week</span></p>
              </div>
            </div>

            <div style={{background:'#111111',border:'1px solid #1f1f1f',borderRadius:'12px',padding:'16px'}}>
              <p style={{color:'#fafafa',fontSize:'13px',fontWeight:'600',margin:'0 0 8px'}}>Manager specialty notes</p>
              <input value={managerSpecialtyNote} readOnly style={{width:'100%',background:'#0f0f0f',border:'1px solid #1f1f1f',borderRadius:'8px',color:'#a1a1aa',padding:'10px 12px',fontSize:'12px'}} />
            </div>
          </>
        )}
      </div>
      <style>{`*{box-sizing:border-box} ::-webkit-scrollbar{width:4px;height:4px} ::-webkit-scrollbar-track{background:#0f0f0f} ::-webkit-scrollbar-thumb{background:#2a2a2a;border-radius:2px}`}</style>
    </div>
  )
}
