import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';

const NotificationCenter = ({ notifications, onClear, onClearAll }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getIcon = (type) => {
    switch (type) {
      case 'decision': return '🧠';
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      case 'processing': return '⏳';
      default: return 'ℹ️';
    }
  };

  const getColor = (type) => {
    switch (type) {
      case 'decision': return 'bg-purple-100/90 text-purple-900 border-purple-300/50';
      case 'success': return 'bg-green-100/90 text-green-900 border-green-300/50';
      case 'warning': return 'bg-yellow-100/90 text-yellow-900 border-yellow-300/50';
      case 'info': return 'bg-blue-100/90 text-blue-900 border-blue-300/50';
      case 'processing': return 'bg-gray-100/90 text-gray-900 border-gray-300/50';
      default: return 'bg-gray-100/90 text-gray-900 border-gray-300/50';
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen ? (
        <Button
          onClick={() => setIsOpen(true)}
          className="relative bg-gradient-to-r from-blue-600/90 to-indigo-600/90 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full p-4 shadow-2xl backdrop-blur-sm border border-white/20 transition-all duration-300 hover:scale-110"
        >
          <span className="text-2xl">🧠</span>
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold shadow-lg animate-pulse">
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      ) : (
        <Card className="w-96 max-h-[600px] shadow-2xl bg-white/90 backdrop-blur-xl border border-white/30">
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-white/30 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 backdrop-blur-sm">
            <CardTitle className="text-lg flex items-center gap-2 font-bold text-gray-900">
              <span className="text-xl">🧠</span>
              AI Agent Notifications
              {unreadCount > 0 && (
                <Badge className="bg-red-500 text-white">{unreadCount} new</Badge>
              )}
            </CardTitle>
            <div className="flex gap-2">
              {notifications.length > 0 && (
                <Button
                  onClick={onClearAll}
                  variant="outline"
                  size="sm"
                  className="text-xs bg-white/60 backdrop-blur-sm border-white/40 hover:bg-white/80"
                >
                  Clear All
                </Button>
              )}
              <Button
                onClick={() => setIsOpen(false)}
                variant="ghost"
                size="sm"
                className="p-1 hover:bg-white/60 rounded-lg"
              >
                ✕
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[500px] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  <div className="text-4xl mb-2">🔔</div>
                  <p>No notifications yet</p>
                </div>
              ) : (
                <div className="space-y-2 p-3">
                  {notifications.map((notif, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl border backdrop-blur-sm ${getColor(notif.type)} ${
                        !notif.read ? 'font-semibold shadow-md ring-2 ring-offset-2 ring-opacity-50' : ''
                      } cursor-pointer hover:shadow-lg transition-all duration-200 transform hover:scale-[1.02]`}
                      onClick={() => onClear(idx)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="text-xl mt-0.5">{getIcon(notif.type)}</div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-bold">{notif.agent || 'System'}</span>
                            <span className="text-xs opacity-70">
                              {new Date(notif.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-sm leading-relaxed">{notif.message}</p>
                          {notif.reasoning && (
                            <div className="mt-2 p-2 bg-white/60 backdrop-blur-sm rounded-lg text-xs italic border border-white/40">
                              <strong>AI Reasoning:</strong> {notif.reasoning}
                            </div>
                          )}
                          {notif.details && (
                            <div className="mt-1 text-xs opacity-75 font-mono">
                              {JSON.stringify(notif.details, null, 2)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default NotificationCenter;
