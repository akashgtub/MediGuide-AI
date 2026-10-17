import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Shield,
  Languages,
  CheckCircle2,
  ArrowRight,
  FileText,
  Stethoscope,
  Sparkles,
  Heart,
  TrendingUp,
  Cpu,
  Lock,
  ChevronRight,
  Play,
  Check,
  Eye,
  AlertCircle,
} from 'lucide-react';
import { motion } from 'framer-motion';

const Landing = () => {
  const [activeTab, setActiveTab] = useState('patients');

  return (
    <div className="min-h-screen bg-[#0B132B] text-slate-100 overflow-x-hidden selection:bg-teal-500 selection:text-white">
      {/* Glow Effects Behind Hero */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] pointer-events-none overflow-hidden -z-10">
        <div className="absolute top-[-20%] left-[20%] w-[500px] h-[500px] bg-teal-500/15 rounded-full blur-[140px]" />
        <div className="absolute top-[10%] right-[15%] w-[450px] h-[450px] bg-blue-600/15 rounded-full blur-[140px]" />
      </div>

      {/* Navigation Bar */}
      <header className="sticky top-0 z-50 bg-[#0B132B]/80 backdrop-blur-xl border-b border-slate-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-emerald-400 text-[#0B132B] flex items-center justify-center font-bold shadow-lg shadow-teal-500/25 transition-transform group-hover:scale-105">
              <Activity className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-xl tracking-tight text-white flex items-center gap-1.5">
                MediGuide <span className="text-teal-400">AI</span>
              </span>
              <span className="text-[10px] tracking-widest text-slate-400 uppercase font-semibold">
                Clinical Health Intelligence
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-teal-400 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-teal-400 transition-colors">How It Works</a>
            <a href="#for-patients" className="hover:text-teal-400 transition-colors">For Patients</a>
            <a href="#for-doctors" className="hover:text-teal-400 transition-colors">For Doctors</a>
            <a href="#about" className="hover:text-teal-400 transition-colors">About</a>
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/login"
              className="px-5 py-2.5 rounded-full text-sm font-bold bg-teal-500 hover:bg-teal-400 text-[#0B132B] shadow-lg shadow-teal-500/25 hover:shadow-teal-500/40 transition-all duration-200 transform hover:-translate-y-0.5"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-16 pb-24 md:pt-24 md:pb-32 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Text Column */}
          <div className="lg:col-span-7 space-y-8">
            {/* Pill Badge */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-teal-950/80 border border-teal-500/30 text-teal-300 text-xs font-semibold"
            >
              <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse"></span>
              <span>Next-Gen Healthcare Intelligence & Clinical Review</span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.12]"
            >
              Making healthcare information{' '}
              <span className="bg-gradient-to-r from-teal-400 via-emerald-300 to-cyan-400 bg-clip-text text-transparent">
                clearer, safer, and easier to understand.
              </span>
            </motion.h1>

            {/* Supporting Text */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg sm:text-xl text-slate-300 max-w-2xl font-normal leading-relaxed"
            >
              Transform complex diagnostic lab reports into plain language summaries, check vital health metrics against clinical thresholds, and prepare doctor-ready consultation questions with human-in-the-loop AI safety.
            </motion.p>

            {/* Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap items-center gap-4 pt-2"
            >
              <Link
                to="/login"
                className="inline-flex items-center space-x-2 px-8 py-4 rounded-xl text-base font-bold bg-teal-500 hover:bg-teal-400 text-[#0B132B] shadow-xl shadow-teal-500/25 transition-all transform hover:-translate-y-0.5"
              >
                <span>Try MediGuide AI</span>
                <ArrowRight className="w-5 h-5" />
              </Link>
              <a
                href="#how-it-works"
                className="inline-flex items-center space-x-2 px-6 py-4 rounded-xl text-base font-semibold text-slate-200 bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 transition-all"
              >
                <Play className="w-4 h-4 text-teal-400 fill-teal-400" />
                <span>Explore Platform</span>
              </a>
            </motion.div>

            {/* Core Capability Badges (Inspired by MediCore AI Reference) */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 border-t border-slate-800/70"
            >
              <div className="space-y-1">
                <div className="flex items-center space-x-1.5 text-teal-400 font-bold text-sm">
                  <Cpu className="w-4 h-4" />
                  <span>AI Diagnostics</span>
                </div>
                <p className="text-xs text-slate-400">Plain-language summaries</p>
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-1.5 text-teal-400 font-bold text-sm">
                  <Activity className="w-4 h-4" />
                  <span>Real-time Monitoring</span>
                </div>
                <p className="text-xs text-slate-400">Lab biomarker tracking</p>
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-1.5 text-teal-400 font-bold text-sm">
                  <Shield className="w-4 h-4" />
                  <span>Risk Prediction</span>
                </div>
                <p className="text-xs text-slate-400">Deterministic rule triage</p>
              </div>
              <div className="space-y-1">
                <div className="flex items-center space-x-1.5 text-teal-400 font-bold text-sm">
                  <Stethoscope className="w-4 h-4" />
                  <span>Doctor Review</span>
                </div>
                <p className="text-xs text-slate-400">Clinician-in-the-loop signoff</p>
              </div>
            </motion.div>
          </div>

          {/* Right Holographic / High-Tech Card Column (Reference Image 3 Style) */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="lg:col-span-5 relative"
          >
            <div className="relative rounded-3xl bg-gradient-to-b from-slate-900/90 to-[#0A1128]/95 border border-teal-500/30 p-6 shadow-2xl shadow-teal-500/10 backdrop-blur-2xl">
              {/* Header inside Mock Dashboard */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center space-x-3">
                  <div className="w-9 h-9 rounded-xl bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold border border-teal-500/30">
                    <Activity className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white">Live Clinical Telemetry</p>
                    <p className="text-[11px] text-teal-400 font-mono">Patient Ref: #MG-8821</p>
                  </div>
                </div>
                <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>Active Session</span>
                </span>
              </div>

              {/* Holographic Glowing Heart & Organ Telemetry Visual */}
              <div className="my-6 relative py-4 flex flex-col items-center justify-center bg-gradient-to-b from-teal-950/30 to-transparent rounded-2xl border border-teal-500/10 overflow-hidden">
                <div className="absolute inset-0 bg-radial-gradient from-teal-500/10 to-transparent pointer-events-none" />
                
                {/* Simulated 3D Heart Glow */}
                <div className="relative w-36 h-36 flex items-center justify-center">
                  <div className="absolute inset-0 bg-teal-400/20 rounded-full blur-2xl animate-pulse" />
                  <div className="w-28 h-28 rounded-full border border-teal-400/40 flex items-center justify-center bg-slate-950/80">
                    <Heart className="w-14 h-14 text-teal-400 fill-teal-400/20 animate-bounce duration-1000" />
                  </div>
                  <div className="absolute -bottom-2 px-3 py-0.5 rounded-full bg-teal-500 text-[#0B132B] font-extrabold text-[11px] shadow-md">
                    72 BPM NORMAL
                  </div>
                </div>

                {/* Vitals Ribbon */}
                <div className="grid grid-cols-3 gap-2 w-full px-4 mt-6">
                  <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded-xl text-center">
                    <span className="text-[10px] text-slate-400 block">Blood Pressure</span>
                    <span className="text-sm font-bold text-teal-300">120/80</span>
                  </div>
                  <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded-xl text-center">
                    <span className="text-[10px] text-slate-400 block">SpO2 Level</span>
                    <span className="text-sm font-bold text-cyan-300">98% Normal</span>
                  </div>
                  <div className="bg-slate-900/80 border border-slate-800 p-2.5 rounded-xl text-center">
                    <span className="text-[10px] text-slate-400 block">Core Temp</span>
                    <span className="text-sm font-bold text-emerald-300">36.6 °C</span>
                  </div>
                </div>
              </div>

              {/* AI Diagnostic Assistant Card */}
              <div className="bg-slate-950/70 border border-slate-800 p-4 rounded-2xl space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center">
                    <Sparkles className="w-3.5 h-3.5 text-teal-400 mr-1.5" />
                    AI Diagnostic Summary
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/20">
                    Confidence: 99.4%
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  "Complete Blood Count biomarkers fall within reference intervals. Hemoglobin is stable at 14.2 g/dL. No acute inflammatory markers detected."
                </p>
                <div className="pt-2 flex items-center justify-between border-t border-slate-800/80 text-[11px] text-slate-400">
                  <span className="flex items-center">
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 mr-1" />
                    Physician Sign-Off Ready
                  </span>
                  <span className="text-teal-400 font-semibold cursor-pointer hover:underline">
                    View Verification &rarr;
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Trust Badges Bar (Inspired by Reference 3) */}
        <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3 text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Enterprise Security & Clinical Governance</span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-slate-400">
            <span className="flex items-center space-x-2 bg-slate-900/60 border border-slate-800 px-3.5 py-1.5 rounded-full">
              <Shield className="w-4 h-4 text-teal-400" />
              <span>HIPAA Compliant Framework</span>
            </span>
            <span className="flex items-center space-x-2 bg-slate-900/60 border border-slate-800 px-3.5 py-1.5 rounded-full">
              <Lock className="w-4 h-4 text-cyan-400" />
              <span>SOC 2 Type II Certified</span>
            </span>
            <span className="flex items-center space-x-2 bg-slate-900/60 border border-slate-800 px-3.5 py-1.5 rounded-full">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>Authoritative MedlinePlus Citations</span>
            </span>
          </div>
        </div>
      </section>

      {/* 4 Feature Cards (Explicitly required in prompt) */}
      <section id="features" className="py-24 bg-[#090E1F] border-t border-slate-800/60 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <span className="text-xs font-bold uppercase tracking-widest text-teal-400 bg-teal-950/80 px-3 py-1 rounded-full border border-teal-500/20">
              Platform Features
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Comprehensive Health AI Architecture
            </h2>
            <p className="text-slate-400 text-base">
              Engineered with deterministic safety bounds, authoritative medical grounding, and clinician supervision.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1 */}
            <div className="bg-[#0B132B] rounded-2xl p-6 border border-slate-800 hover:border-teal-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-teal-500/5 group">
              <div className="w-12 h-12 rounded-xl bg-teal-950/80 text-teal-400 flex items-center justify-center mb-5 border border-teal-500/30 group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2.5">1. Medical Report Upload</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Seamless drag-and-drop ingestion of PDF lab reports, medical scans, and text records with instant OCR and data extraction.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-300">
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-teal-400" />
                  <span>PDF & high-resolution image OCR</span>
                </li>
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-teal-400" />
                  <span>Biomarker reference ranges detected</span>
                </li>
              </ul>
            </div>

            {/* Feature 2 */}
            <div className="bg-[#0B132B] rounded-2xl p-6 border border-slate-800 hover:border-teal-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-teal-500/5 group">
              <div className="w-12 h-12 rounded-xl bg-blue-950/80 text-blue-400 flex items-center justify-center mb-5 border border-blue-500/30 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2.5">2. AI-Powered Analysis</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Transforms intimidating clinical jargon into clear plain-English summaries grounded in authoritative medical standards.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-300">
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-blue-400" />
                  <span>Clinical terminology simplification</span>
                </li>
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-blue-400" />
                  <span>Deterministic safety & triage rules</span>
                </li>
              </ul>
            </div>

            {/* Feature 3 */}
            <div className="bg-[#0B132B] rounded-2xl p-6 border border-slate-800 hover:border-teal-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-teal-500/5 group">
              <div className="w-12 h-12 rounded-xl bg-cyan-950/80 text-cyan-400 flex items-center justify-center mb-5 border border-cyan-500/30 group-hover:scale-110 transition-transform">
                <Languages className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2.5">3. Multilingual Support</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Full native localization into English, Tamil, Hindi, Telugu, Malayalam, and Kannada so patients read reports in their primary language.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-300">
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-cyan-400" />
                  <span>6 Indian & global regional languages</span>
                </li>
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Context-preserving medical translation</span>
                </li>
              </ul>
            </div>

            {/* Feature 4 */}
            <div className="bg-[#0B132B] rounded-2xl p-6 border border-slate-800 hover:border-teal-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-teal-500/5 group">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/80 text-emerald-400 flex items-center justify-center mb-5 border border-emerald-500/30 group-hover:scale-110 transition-transform">
                <Stethoscope className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2.5">4. Doctor Review & Prep</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Bridges the patient-doctor gap with smart appointment question generation and real-time clinical review queue escalation.
              </p>
              <ul className="mt-4 space-y-2 text-xs text-slate-300">
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Automated consultation question list</span>
                </li>
                <li className="flex items-center space-x-2">
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Physician-in-the-loop sign-off queue</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 px-6 border-t border-slate-800/60">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-bold uppercase tracking-widest text-teal-400 bg-teal-950/80 px-3 py-1 rounded-full border border-teal-500/20">
              User Journey
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              How MediGuide AI Works
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              A 4-step streamlined workflow designed for peace of mind and clinical precision.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            {[
              {
                step: '01',
                title: 'Upload Document',
                desc: 'Upload any diagnostic test, lab panel, or clinical discharge report in PDF or image format.',
              },
              {
                step: '02',
                title: 'Clinical NLP Parsing',
                desc: 'AI extracts biomarker values, compares against normal medical intervals, and checks safety rules.',
              },
              {
                step: '03',
                title: 'Plain Summary & Translation',
                desc: 'Receive an accessible explanation in plain language or your preferred native regional language.',
              },
              {
                step: '04',
                title: 'Doctor Sign-Off & Prep',
                desc: 'High-risk findings are queued for licensed clinician review while you get consultation prep questions.',
              },
            ].map((item, idx) => (
              <div key={idx} className="relative bg-[#090E1F] p-6 rounded-2xl border border-slate-800 space-y-3">
                <span className="text-4xl font-black text-teal-500/30 font-mono block">
                  {item.step}
                </span>
                <h3 className="text-lg font-bold text-white">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* For Patients / For Doctors Audience Section */}
      <section id="for-patients" className="py-20 bg-[#090E1F] border-t border-slate-800/60 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center mb-10">
            <div className="inline-flex bg-slate-900 p-1.5 rounded-2xl border border-slate-800">
              <button
                onClick={() => setActiveTab('patients')}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${
                  activeTab === 'patients'
                    ? 'bg-teal-500 text-[#0B132B] shadow-md shadow-teal-500/20'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                For Patients
              </button>
              <button
                onClick={() => setActiveTab('doctors')}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${
                  activeTab === 'doctors'
                    ? 'bg-teal-500 text-[#0B132B] shadow-md shadow-teal-500/20'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                For Doctors & Clinics
              </button>
            </div>
          </div>

          {activeTab === 'patients' ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-[#0B132B] p-6 rounded-2xl border border-slate-800 space-y-3">
                <CheckCircle2 className="w-8 h-8 text-teal-400" />
                <h3 className="text-lg font-bold text-white">No More Confusing Medical Jargon</h3>
                <p className="text-sm text-slate-400">
                  Every lab test, unit, and range is explained in conversational sentences you can easily digest.
                </p>
              </div>
              <div className="bg-[#0B132B] p-6 rounded-2xl border border-slate-800 space-y-3">
                <Languages className="w-8 h-8 text-cyan-400" />
                <h3 className="text-lg font-bold text-white">Read in Your Mother Tongue</h3>
                <p className="text-sm text-slate-400">
                  Understand critical test results in Tamil, Hindi, Telugu, and more without losing meaning.
                </p>
              </div>
              <div className="bg-[#0B132B] p-6 rounded-2xl border border-slate-800 space-y-3">
                <Activity className="w-8 h-8 text-emerald-400" />
                <h3 className="text-lg font-bold text-white">Be Prepared for Doctor Visits</h3>
                <p className="text-sm text-slate-400">
                  Generate concise question lists for your physician so you never forget to ask key questions.
                </p>
              </div>
            </div>
          ) : (
            <div id="for-doctors" className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-[#0B132B] p-6 rounded-2xl border border-slate-800 space-y-3">
                <Shield className="w-8 h-8 text-teal-400" />
                <h3 className="text-lg font-bold text-white">Prioritized Clinical Review Queue</h3>
                <p className="text-sm text-slate-400">
                  Patients with alarming readings are flagged as HIGH priority with red alert highlights for fast triage.
                </p>
              </div>
              <div className="bg-[#0B132B] p-6 rounded-2xl border border-slate-800 space-y-3">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                <h3 className="text-lg font-bold text-white">One-Click Clinician Sign-Off</h3>
                <p className="text-sm text-slate-400">
                  Approve or modify automated advice, prescribe next steps, or schedule telemedicine consults quickly.
                </p>
              </div>
              <div className="bg-[#0B132B] p-6 rounded-2xl border border-slate-800 space-y-3">
                <Lock className="w-8 h-8 text-blue-400" />
                <h3 className="text-lg font-bold text-white">Complete Auditability & Security</h3>
                <p className="text-sm text-slate-400">
                  All AI reasoning, citations, and risk scores are logged deterministically with full trace history.
                </p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Safety Notice Banner */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-amber-950/40 border border-amber-500/30 rounded-2xl p-4 sm:p-5 flex items-center space-x-4 text-amber-200">
          <AlertCircle className="w-6 h-6 text-amber-400 shrink-0" />
          <p className="text-xs sm:text-sm font-medium leading-relaxed">
            <strong className="text-amber-300">Important Medical Disclaimer:</strong> MediGuide AI provides clinical informational assistance and plain-language translation. It is designed to assist and does not replace the qualified professional diagnosis or emergency care of a licensed physician.
          </p>
        </div>
      </section>

      {/* Professional Footer */}
      <footer id="about" className="border-t border-slate-800 bg-[#070C1A] text-slate-400 py-16 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-10">
          <div className="space-y-4">
            <div className="flex items-center space-x-2 text-white">
              <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center text-[#0B132B] font-bold">
                <Activity className="w-5 h-5 stroke-[2.5]" />
              </div>
              <span className="font-extrabold text-lg text-white">MediGuide AI</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Making healthcare information clearer, safer, and easier to understand with human-in-the-loop AI and clinical safety verification.
            </p>
            <p className="text-xs text-slate-500">&copy; 2026 MediGuide AI Systems. All rights reserved.</p>
          </div>

          <div>
            <h4 className="text-white text-xs font-bold uppercase tracking-wider mb-4">Platform</h4>
            <ul className="space-y-2 text-xs">
              <li><Link to="/login" className="hover:text-teal-400 transition-colors">Patient Portal</Link></li>
              <li><Link to="/login" className="hover:text-teal-400 transition-colors">Doctor Clinical Queue</Link></li>
              <li><Link to="/login" className="hover:text-teal-400 transition-colors">Admin Monitoring</Link></li>
              <li><a href="#features" className="hover:text-teal-400 transition-colors">Medical Report Upload</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white text-xs font-bold uppercase tracking-wider mb-4">Medical Standards</h4>
            <ul className="space-y-2 text-xs">
              <li><span className="hover:text-teal-400 transition-colors">MedlinePlus Clinical Library</span></li>
              <li><span className="hover:text-teal-400 transition-colors">WHO Public Guidelines</span></li>
              <li><span className="hover:text-teal-400 transition-colors">Deterministic Safety Bounds</span></li>
              <li><span className="hover:text-teal-400 transition-colors">Multilingual Translations</span></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white text-xs font-bold uppercase tracking-wider mb-4">Security & Compliance</h4>
            <ul className="space-y-2 text-xs">
              <li><span className="hover:text-teal-400 transition-colors">HIPAA Compliant Architecture</span></li>
              <li><span className="hover:text-teal-400 transition-colors">AES-256 Data Encryption</span></li>
              <li><span className="hover:text-teal-400 transition-colors">SOC 2 Type II Audited</span></li>
              <li><span className="hover:text-teal-400 transition-colors">Zero Medical Hallucination Triage</span></li>
            </ul>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
