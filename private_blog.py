import React, { useState, useEffect, useRef } from 'react';
import { 
  BookOpen, 
  Feather, 
  Aperture, 
  PenTool, 
  X, 
  ArrowLeft, 
  Heart, 
  MessageCircle, 
  Wind, 
  Calendar,
  Layers,
  Send
} from 'lucide-react';

// --- Mock Data ---

const INITIAL_POSTS = [
  {
    id: 1,
    type: 'blog',
    title: '周二的雨和便利店',
    date: '2023-10-24',
    content: '今天下了一整天的雨。躲进便利店的时候，眼镜上全是雾气。买了一份热关东煮，萝卜煮得很透。生活偶尔需要这种微小的确幸，像是在漫长的灰暗里擦亮了一根火柴。',
    weather: 'rainy',
    resonance: 12
  },
  {
    id: 2,
    type: 'writing',
    category: 'Melancholy', // 忧郁/失恋
    title: '蓝色的回信',
    date: '2023-09-15',
    content: '你说海是倒过来的天。后来我每次看海，都觉得是在坠落。我们在那个夏天把话说尽了，剩下的日子只能用沉默来填补。即使现在想起你，心里的某块地方还是会像被钝器击打一样闷响。',
    resonance: 45
  },
  {
    id: 3,
    type: 'gallery',
    title: '现代性的流动与静止',
    subtitle: '关于时间感知的随笔',
    date: '2023-08-01',
    content: '在这个加速主义的时代，静止变成了一种奢侈品。我们不停地刷新，试图抓住当下的尾巴，却在信息流中失去了对“永恒”的感知能力。或许，真正的反抗不是停下脚步，而是学会在洪流中建立自己的锚点。',
    resonance: 89
  },
  {
    id: 4,
    type: 'blog',
    title: '重新整理书架',
    date: '2023-10-22',
    content: '翻出了几本旧书，纸张已经泛黄了。那是大学时期买的，那时候总觉得只要买书就是在学习。现在看来，书架更像是展示给自己的“理想自我”。',
    weather: 'sunny',
    resonance: 5
  },
  {
    id: 5,
    type: 'writing',
    category: 'Hope', // 希望/工作
    title: '黎明前的微光',
    date: '2023-11-01',
    content: '项目上线的最后一刻，所有人都累瘫在椅子上。窗外的天空泛起鱼肚白，那一刻没有欢呼，只有一种沉甸甸的宁静。努力是有回响的，哪怕它来得很慢。',
    resonance: 23
  }
];

// --- Utility Components ---

const FadeIn = ({ children, delay = 0 }) => (
  <div className="animate-fade-in opacity-0" style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}>
    {children}
  </div>
);

// --- Feature Components ---

// 1. Admin Editor Modal
const Editor = ({ isOpen, onClose, onPublish }) => {
  const [type, setType] = useState('blog');
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('General');

  if (!isOpen) return null;

  const handlePublish = () => {
    if (!content) return;
    const newPost = {
      id: Date.now(),
      type,
      title: title || '无题',
      date: new Date().toISOString().split('T')[0],
      content,
      category: type === 'writing' ? category : undefined,
      resonance: 0
    };
    onPublish(newPost);
    // Reset
    setContent('');
    setTitle('');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/90 backdrop-blur-sm transition-all">
      <div className="w-full max-w-2xl bg-white p-8 shadow-2xl rounded-sm border border-stone-100">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-serif text-stone-800">创作 (Admin Mode)</h2>
          <button onClick={onClose}><X className="text-stone-400 hover:text-stone-800" /></button>
        </div>

        <div className="space-y-4">
          <div className="flex gap-4 mb-4">
            {['blog', 'writing', 'gallery'].map((t) => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`px-4 py-2 text-sm rounded-full transition-colors ${
                  type === t ? 'bg-stone-800 text-white' : 'bg-stone-100 text-stone-600'
                }`}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          <input
            type="text"
            placeholder="标题..."
            className="w-full text-2xl font-serif border-b border-stone-200 py-2 focus:outline-none focus:border-stone-500 bg-transparent placeholder-stone-300"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          {type === 'writing' && (
            <select 
              className="w-full p-2 bg-stone-50 border-none text-stone-600 text-sm focus:ring-0"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="Melancholy">失恋/忧郁 (Melancholy)</option>
              <option value="Hope">希望/工作 (Hope)</option>
              <option value="Rage">愤怒 (Rage)</option>
            </select>
          )}

          <textarea
            className="w-full h-64 p-4 bg-stone-50 text-stone-700 font-serif leading-loose focus:outline-none resize-none"
            placeholder="在这里记录你的灵魂..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />

          <div className="flex justify-end pt-4">
            <button 
              onClick={handlePublish}
              className="px-8 py-3 bg-stone-800 text-white hover:bg-stone-700 transition-colors font-sans text-sm tracking-widest"
            >
              发布
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// 2. Article Reader (Immersive View)
const ArticleReader = ({ post, onClose }) => {
  const [resonanceCount, setResonanceCount] = useState(post.resonance);
  const [hasResonated, setHasResonated] = useState(false);
  const [echoText, setEchoText] = useState('');
  const [echoSent, setEchoSent] = useState(false);

  const handleResonate = () => {
    if (!hasResonated) {
      setResonanceCount(c => c + 1);
      setHasResonated(true);
    }
  };

  const handleEcho = () => {
    if (echoText.trim()) {
      setEchoSent(true);
      setTimeout(() => {
        setEchoText('');
        setEchoSent(false); // Reset for demo
      }, 3000);
    }
  };

  // Dynamic background based on category for Writing type
  const getBgClass = () => {
    if (post.type === 'writing') {
      if (post.category === 'Melancholy') return 'bg-slate-50';
      if (post.category === 'Hope') return 'bg-amber-50/30';
      return 'bg-white';
    }
    return 'bg-white';
  };

  return (
    <div className={`fixed inset-0 z-40 overflow-y-auto ${getBgClass()} transition-colors duration-1000`}>
      <div className="max-w-3xl mx-auto px-6 py-20 md:py-32 min-h-screen relative">
        <button 
          onClick={onClose} 
          className="fixed top-8 left-8 md:top-12 md:left-20 p-2 rounded-full hover:bg-black/5 transition-colors group"
        >
          <ArrowLeft className="w-6 h-6 text-stone-400 group-hover:text-stone-800" />
        </button>

        <article className="prose prose-stone prose-lg mx-auto">
          <FadeIn>
            <div className="text-center mb-16">
              <span className="text-xs tracking-[0.2em] text-stone-400 uppercase">{post.type} · {post.date}</span>
              <h1 className="text-4xl md:text-5xl font-serif text-stone-900 mt-6 mb-4 leading-tight">{post.title}</h1>
              {post.type === 'writing' && (
                <span className="inline-block px-3 py-1 bg-stone-100 text-stone-500 text-xs rounded-full">{post.category}</span>
              )}
            </div>
          </FadeIn>

          <FadeIn delay={200}>
            <div className="font-serif text-lg leading-loose text-stone-700 whitespace-pre-wrap">
              {post.content}
            </div>
          </FadeIn>

          {/* Interaction Section */}
          <FadeIn delay={500}>
            <div className="mt-24 pt-12 border-t border-stone-100 flex flex-col items-center space-y-12">
              
              {/* Resonance */}
              <button 
                onClick={handleResonate}
                className={`group flex items-center space-x-3 transition-all duration-500 ${hasResonated ? 'scale-110' : 'hover:scale-105'}`}
              >
                <div className={`p-4 rounded-full ${hasResonated ? 'bg-red-50 text-red-500 shadow-inner' : 'bg-stone-50 text-stone-400 group-hover:bg-white group-hover:shadow-lg'}`}>
                  <Heart className={`w-6 h-6 ${hasResonated ? 'fill-current' : ''}`} />
                </div>
                <span className="text-sm font-sans text-stone-400 tracking-widest">
                  {hasResonated ? '已共鸣' : '共鸣'} {resonanceCount}
                </span>
              </button>

              {/* Echo (Private Comment) */}
              <div className="w-full max-w-md">
                <div className="text-center mb-4">
                  <h3 className="text-sm font-serif text-stone-500">Echo Hole (私密回声)</h3>
                  <p className="text-xs text-stone-300 mt-1">只有作者能听见你的声音</p>
                </div>
                {echoSent ? (
                  <div className="text-center p-4 text-stone-500 text-sm bg-stone-50 rounded italic">
                    回声已飘入深海...
                  </div>
                ) : (
                  <div className="relative">
                    <textarea 
                      value={echoText}
                      onChange={(e) => setEchoText(e.target.value)}
                      className="w-full p-4 bg-transparent border border-stone-200 rounded-sm focus:border-stone-400 focus:outline-none text-sm text-stone-600 resize-none font-serif"
                      rows="3"
                      placeholder="在这里写下你的回响..."
                    />
                    <button 
                      onClick={handleEcho}
                      className="absolute bottom-4 right-4 text-stone-400 hover:text-stone-800"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>

            </div>
          </FadeIn>
        </article>
      </div>
    </div>
  );
};

// 3. Blog List (The Stream)
const BlogSection = ({ posts, onRead }) => (
  <div className="max-w-xl mx-auto py-12 px-6">
    <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-px bg-stone-200 -z-10 hidden md:block"></div>
    {posts.map((post, idx) => (
      <FadeIn key={post.id} delay={idx * 100}>
        <div className="mb-16 relative md:flex md:justify-between group cursor-pointer" onClick={() => onRead(post)}>
          {/* Timeline Dot */}
          <div className="hidden md:block absolute left-1/2 -ml-[5px] w-[9px] h-[9px] rounded-full bg-stone-300 border-2 border-white mt-2 group-hover:bg-stone-800 transition-colors"></div>
          
          <div className="md:w-[45%] md:text-right md:pr-8 mb-2 md:mb-0">
            <span className="text-xs font-bold tracking-widest text-stone-400">{post.date}</span>
            <div className="text-stone-300 text-xs mt-1">{post.weather === 'rainy' ? '🌧' : '☀'}</div>
          </div>
          <div className="md:w-[45%] md:pl-8">
            <h3 className="text-lg font-serif text-stone-800 mb-2 group-hover:text-black transition-colors">{post.title}</h3>
            <p className="text-stone-500 text-sm line-clamp-3 leading-relaxed font-serif">
              {post.content}
            </p>
          </div>
        </div>
      </FadeIn>
    ))}
  </div>
);

// 4. Writing List (The Prism)
const WritingSection = ({ posts, onRead }) => {
  const [filter, setFilter] = useState('All');
  const categories = ['All', 'Melancholy', 'Hope', 'Rage'];

  const filteredPosts = filter === 'All' ? posts : posts.filter(p => p.category === filter);

  // Background tint based on active filter
  const getTint = () => {
    if (filter === 'Melancholy') return 'bg-slate-50/50';
    if (filter === 'Hope') return 'bg-amber-50/50';
    if (filter === 'Rage') return 'bg-red-50/50';
    return '';
  };

  return (
    <div className={`min-h-[80vh] transition-colors duration-1000 ${getTint()}`}>
      <div className="max-w-4xl mx-auto py-12 px-6">
        {/* Filter Tabs */}
        <div className="flex justify-center space-x-8 mb-16">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`text-sm tracking-widest uppercase transition-all duration-300 ${
                filter === cat 
                  ? 'text-stone-900 border-b border-stone-900 pb-1' 
                  : 'text-stone-400 hover:text-stone-600'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Masonry-ish Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {filteredPosts.map((post, idx) => (
            <FadeIn key={post.id} delay={idx * 100}>
              <div 
                onClick={() => onRead(post)}
                className="bg-white p-8 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-500 cursor-pointer border border-stone-50"
              >
                <div className="flex justify-between items-start mb-6">
                  <span className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded-sm ${
                    post.category === 'Melancholy' ? 'bg-slate-100 text-slate-600' :
                    post.category === 'Hope' ? 'bg-amber-100 text-amber-600' :
                    'bg-stone-100 text-stone-600'
                  }`}>
                    {post.category}
                  </span>
                  <span className="text-xs text-stone-300">{post.date}</span>
                </div>
                <h3 className="text-xl font-serif text-stone-800 mb-4">{post.title}</h3>
                <p className="text-stone-500 text-sm leading-7 line-clamp-4 font-serif">
                  {post.content}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </div>
  );
};

// 5. Gallery List (The Exhibition)
const GallerySection = ({ posts, onRead }) => (
  <div className="max-w-3xl mx-auto py-20 px-6">
    {posts.map((post, idx) => (
      <FadeIn key={post.id} delay={idx * 200}>
        <div 
          onClick={() => onRead(post)}
          className="mb-32 group cursor-pointer border-l-2 border-transparent hover:border-stone-900 pl-6 transition-all duration-500"
        >
          <div className="text-xs tracking-[0.3em] text-stone-400 uppercase mb-4">Exhibit No. 0{idx + 1}</div>
          <h2 className="text-4xl md:text-6xl font-serif text-stone-900 mb-6 leading-tight group-hover:italic transition-all">
            {post.title}
          </h2>
          {post.subtitle && (
            <p className="text-xl text-stone-500 font-serif italic mb-6">{post.subtitle}</p>
          )}
          <div className="h-px w-12 bg-stone-300 group-hover:w-24 transition-all duration-700"></div>
          <div className="mt-6 text-stone-400 text-sm font-sans tracking-wide opacity-0 group-hover:opacity-100 transition-opacity duration-500">
            Click to View Thought
          </div>
        </div>
      </FadeIn>
    ))}
    
    <div className="text-center py-20 text-stone-300 text-xs tracking-widest">
      END OF EXHIBITION
    </div>
  </div>
);

// --- Main App Component ---

export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // home, blog, writing, gallery
  const [posts, setPosts] = useState(INITIAL_POSTS);
  const [readingPost, setReadingPost] = useState(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  // Global style injection for custom animations
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fade-in {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .animate-fade-in {
        animation-name: fade-in;
        animation-duration: 0.8s;
        animation-timing-function: cubic-bezier(0.2, 0.8, 0.2, 1);
      }
      /* Custom scrollbar for webkit */
      ::-webkit-scrollbar { width: 6px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb { background: #e7e5e4; border-radius: 3px; }
      ::-webkit-scrollbar-thumb:hover { background: #a8a29e; }

      /* --- 字体优化 (Font Customization) --- */
      
      /* 小字/UI (Notion/Apple Style): 干净、现代、系统原生 */
      body, .font-sans {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei" !important;
      }

      /* 文学/标题 (Simple Classical): 宋体优先，营造书卷气 */
      .font-serif {
        font-family: "Songti SC", "Noto Serif SC", "SimSun", "STSong", "Times New Roman", "Lyon-Text", "Georgia", serif !important;
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  const handlePublish = (newPost) => {
    setPosts([newPost, ...posts]);
  };

  const filteredPosts = (type) => posts.filter(p => p.type === type);

  // Home Page Component
  const Home = () => (
    <div className="min-h-screen flex flex-col justify-center items-center relative overflow-hidden">
      <FadeIn>
        <h1 className="text-6xl md:text-8xl font-serif text-stone-900 tracking-tighter mb-4 text-center">
          TRIAD
          <span className="text-stone-300 text-6xl">.</span>
        </h1>
        <p className="text-center text-stone-500 font-serif italic mb-16 tracking-wide">
          Time · Emotion · Thought
        </p>
      </FadeIn>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-24 text-center z-10">
        <button 
          onClick={() => setActiveTab('blog')}
          className="group flex flex-col items-center space-y-4 transition-transform hover:-translate-y-2"
        >
          <div className="p-6 rounded-full bg-stone-50 group-hover:bg-stone-100 transition-colors">
            <Feather className="w-6 h-6 text-stone-600" />
          </div>
          <span className="font-sans text-xs tracking-[0.2em] uppercase text-stone-400 group-hover:text-stone-900 transition-colors">Blogs</span>
        </button>

        <button 
          onClick={() => setActiveTab('writing')}
          className="group flex flex-col items-center space-y-4 transition-transform hover:-translate-y-2"
        >
          <div className="p-6 rounded-full bg-stone-50 group-hover:bg-stone-100 transition-colors">
            <BookOpen className="w-6 h-6 text-stone-600" />
          </div>
          <span className="font-sans text-xs tracking-[0.2em] uppercase text-stone-400 group-hover:text-stone-900 transition-colors">Writing</span>
        </button>

        <button 
          onClick={() => setActiveTab('gallery')}
          className="group flex flex-col items-center space-y-4 transition-transform hover:-translate-y-2"
        >
          <div className="p-6 rounded-full bg-stone-50 group-hover:bg-stone-100 transition-colors">
            <Aperture className="w-6 h-6 text-stone-600" />
          </div>
          <span className="font-sans text-xs tracking-[0.2em] uppercase text-stone-400 group-hover:text-stone-900 transition-colors">Gallery</span>
        </button>
      </div>

      <div className="absolute bottom-12 text-stone-300 text-[10px] tracking-widest">
        EST. 2024 · PERSONAL SPACE
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-white text-stone-800 selection:bg-stone-200 selection:text-stone-900 font-sans">
      
      {/* Navigation (Only show if not on home) */}
      {activeTab !== 'home' && !readingPost && (
        <nav className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-stone-100">
          <div className="max-w-6xl mx-auto px-6 h-20 flex justify-between items-center">
            <button 
              onClick={() => setActiveTab('home')}
              className="text-xl font-serif font-bold tracking-tight hover:opacity-70 transition-opacity"
            >
              TRIAD.
            </button>
            <div className="flex space-x-8">
              {['blog', 'writing', 'gallery'].map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveTab(t)}
                  className={`text-xs uppercase tracking-widest transition-colors ${
                    activeTab === t ? 'text-stone-900 font-bold' : 'text-stone-400 hover:text-stone-600'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </nav>
      )}

      {/* Main Content Area */}
      <main className="min-h-screen">
        {readingPost ? (
          <ArticleReader post={readingPost} onClose={() => setReadingPost(null)} />
        ) : (
          <>
            {activeTab === 'home' && <Home />}
            
            {activeTab === 'blog' && (
              <div className="animate-fade-in">
                <header className="py-20 text-center">
                  <h2 className="text-3xl font-serif text-stone-800 mb-2">流动的日常</h2>
                  <p className="text-xs text-stone-400 tracking-widest uppercase">The Stream of Time</p>
                </header>
                <BlogSection posts={filteredPosts('blog')} onRead={setReadingPost} />
              </div>
            )}

            {activeTab === 'writing' && (
              <div className="animate-fade-in">
                <header className="py-20 text-center">
                  <h2 className="text-3xl font-serif text-stone-800 mb-2">情感棱镜</h2>
                  <p className="text-xs text-stone-400 tracking-widest uppercase">Prism of Emotions</p>
                </header>
                <WritingSection posts={filteredPosts('writing')} onRead={setReadingPost} />
              </div>
            )}

            {activeTab === 'gallery' && (
              <div className="animate-fade-in">
                <header className="py-20 text-center">
                  <h2 className="text-3xl font-serif text-stone-800 mb-2">思想展厅</h2>
                  <p className="text-xs text-stone-400 tracking-widest uppercase">The Exhibition</p>
                </header>
                <GallerySection posts={filteredPosts('gallery')} onRead={setReadingPost} />
              </div>
            )}
          </>
        )}
      </main>

      {/* Admin Trigger (Bottom Right Corner) */}
      <button 
        onClick={() => setIsEditorOpen(true)}
        className="fixed bottom-8 right-8 p-3 bg-black text-white rounded-full shadow-lg hover:scale-110 transition-transform z-30 opacity-20 hover:opacity-100"
        title="Admin Write"
      >
        <PenTool className="w-5 h-5" />
      </button>

      {/* Modals */}
      <Editor 
        isOpen={isEditorOpen} 
        onClose={() => setIsEditorOpen(false)} 
        onPublish={handlePublish} 
      />
    </div>
  );
}
