import { Link } from 'react-router-dom';
import { Activity, Shield, Languages, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const Landing = () => {
  return (
    <div className="min-h-screen bg-white">
      <header className="px-6 py-4 flex justify-between items-center border-b border-slate-100">
        <div className="flex items-center space-x-2 text-teal-600">
          <Activity className="w-6 h-6" />
          <span className="font-bold text-xl text-slate-800">MediGuide AI</span>
        </div>
        <div className="space-x-4">
          <Link to="/login" className="text-slate-600 hover:text-teal-600 font-medium transition-colors">Sign In</Link>
          <Link to="/login" className="bg-teal-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-teal-700 transition-colors">Get Started</Link>
        </div>
      </header>

      <main>
        <section className="max-w-5xl mx-auto px-6 py-20 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <h1 className="text-5xl md:text-6xl font-bold text-slate-900 mb-6 tracking-tight">
              Making healthcare information <br/>
              <span className="text-teal-600">clearer, safer, and easier to understand.</span>
            </h1>
            <p className="text-xl text-slate-500 mb-10 max-w-2xl mx-auto">
              Upload medical reports, understand complex terminology, and prepare for your next doctor's visit with our secure AI assistant.
            </p>
            <Link to="/login" className="bg-teal-600 text-white px-8 py-3 rounded-full text-lg font-medium shadow-md hover:shadow-lg hover:bg-teal-700 transition-all">
              Try MediGuide AI
            </Link>
          </motion.div>
        </section>

        <section className="bg-slate-50 py-20">
          <div className="max-w-5xl mx-auto px-6">
            <h2 className="text-3xl font-bold text-center text-slate-800 mb-12">Core Features</h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                { title: 'Patient-Friendly Summaries', desc: 'Complex medical jargon simplified.', icon: <CheckCircle className="w-6 h-6 text-teal-500" /> },
                { title: 'Safe AI Assistance', desc: 'Secure, human-in-the-loop assistance.', icon: <Shield className="w-6 h-6 text-blue-500" /> },
                { title: 'Multilingual Support', desc: 'Understand reports in your language.', icon: <Languages className="w-6 h-6 text-amber-500" /> }
              ].map((f, i) => (
                <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                  <div className="mb-4">{f.icon}</div>
                  <h3 className="text-xl font-bold text-slate-800 mb-2">{f.title}</h3>
                  <p className="text-slate-500">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="max-w-3xl mx-auto px-6 py-16 text-center">
          <div className="bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-lg flex items-center justify-center space-x-2">
            <Shield className="w-5 h-5" />
            <p className="font-medium">MediGuide AI provides informational assistance and does not replace qualified healthcare professionals.</p>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Landing;
