import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card';
import { ArrowRight, Users, FileText, Briefcase, Clock, TrendingUp, Activity } from 'lucide-react';

const Home = () => {
  const quickActions = [
    {
      title: 'Create Job Profile',
      description: 'Use AI chat or upload PDF to create job profiles',
      icon: '📄',
      link: '/create-job-profile',
      gradient: 'from-blue-500 to-cyan-500',
      shadow: 'shadow-blue-500/20',
    },
    {
      title: 'View Profiles',
      description: 'Manage and approve job profiles',
      icon: '📂',
      link: '/profiles',
      gradient: 'from-purple-500 to-pink-500',
      shadow: 'shadow-purple-500/20',
    },
    {
      title: 'Job Portal',
      description: 'View active job listings',
      icon: '💼',
      link: '/jobs',
      gradient: 'from-indigo-500 to-blue-500',
      shadow: 'shadow-indigo-500/20',
    },
    {
      title: 'Applicants',
      description: 'Review candidate applications',
      icon: '👥',
      link: '/applicants',
      gradient: 'from-emerald-500 to-teal-500',
      shadow: 'shadow-emerald-500/20',
    },
  ];

  const stats = [
    { label: 'Active Jobs', value: '12', icon: Briefcase, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Total Applicants', value: '148', icon: Users, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Pending Reviews', value: '5', icon: Clock, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Interviews Today', value: '3', icon: Activity, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  ];

  return (
    <main className="flex-1 space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 to-indigo-600 p-8 lg:p-12 shadow-2xl shadow-blue-900/20">
        <div className="absolute top-0 right-0 -mt-20 -mr-20 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>

        <div className="relative z-10 max-w-3xl">
          <h1 className="text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
            Welcome back, <span className="text-blue-200">HR Manager</span>
          </h1>
          <p className="text-lg text-blue-100 mb-8 max-w-2xl leading-relaxed">
            Your AI-powered recruitment dashboard is ready. You have <span className="font-bold text-white">5 pending reviews</span> and <span className="font-bold text-white">3 interviews</span> scheduled for today.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              to="/create-job-profile"
              className="px-6 py-3 bg-white text-blue-600 rounded-xl font-semibold shadow-lg hover:shadow-xl hover:bg-blue-50 transition-all duration-200 flex items-center"
            >
              Create New Profile <ArrowRight size={18} className="ml-2" />
            </Link>
            <Link
              to="/applicants"
              className="px-6 py-3 bg-blue-700/50 text-white rounded-xl font-semibold backdrop-blur-sm hover:bg-blue-700/70 transition-all duration-200"
            >
              View Applicants
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <Card key={index} className="border-none shadow-lg hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-xl">
            <CardContent className="p-6 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">{stat.label}</p>
                <h3 className="text-3xl font-bold text-gray-900">{stat.value}</h3>
              </div>
              <div className={`w-12 h-12 rounded-2xl ${stat.bg} flex items-center justify-center ${stat.color}`}>
                <stat.icon size={24} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions Grid */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center">
          <TrendingUp className="mr-2 text-blue-600" size={24} />
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action, index) => (
            <Link
              key={index}
              to={action.link}
              className="group"
            >
              <Card className={`h-full border-none shadow-lg hover:shadow-xl transition-all duration-300 bg-white/80 backdrop-blur-xl overflow-hidden relative group-hover:-translate-y-1`}>
                <div className={`absolute top-0 left-0 w-1 h-full bg-gradient-to-b ${action.gradient}`}></div>
                <CardContent className="p-6">
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${action.gradient} flex items-center justify-center text-2xl mb-4 shadow-lg ${action.shadow} group-hover:scale-110 transition-transform duration-300 text-white`}>
                    {action.icon}
                  </div>
                  <CardTitle className="text-lg font-bold mb-2 text-gray-900 group-hover:text-blue-600 transition-colors">
                    {action.title}
                  </CardTitle>
                  <CardDescription className="text-gray-500 text-sm leading-relaxed">
                    {action.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
};

export default Home;
