import { Route, Switch } from "wouter";
import { Toaster } from "@/components/ui/sonner";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import RouteAnalysis from "@/pages/RouteAnalysis";
import RiskAnalysis from "@/pages/RiskAnalysis";
import Alerts from "@/pages/Alerts";
import About from "@/pages/About";
import LandslideDetection from "@/pages/LandslideDetection";
import { AnalysisProvider } from "@/contexts/AnalysisContext";

function NotFound() { return <div className="grid min-h-screen place-items-center bg-[#f4f9fc] p-6 text-center"><div><div className="font-mono text-xs uppercase tracking-[0.18em] text-[#3979f6]">404 / route not found</div><h1 className="mt-3 text-4xl font-semibold text-[#0a1858]">This corridor is unmapped.</h1><a className="mt-6 inline-block rounded-xl bg-[#080d4d] px-5 py-3 text-sm font-semibold text-white" href="/">Return to NAVEXA</a></div></div>; }

export default function App() { return <AnalysisProvider><Toaster position="top-right"/><Switch><Route path="/" component={Landing}/><Route path="/login" component={Login}/><Route path="/dashboard" component={Dashboard}/><Route path="/route-analysis" component={RouteAnalysis}/><Route path="/risk-analysis" component={RiskAnalysis}/><Route path="/landslide-detection" component={LandslideDetection}/><Route path="/alerts" component={Alerts}/><Route path="/about" component={About}/><Route component={NotFound}/></Switch></AnalysisProvider>; }
