import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X, Brain, CheckCircle, AlertCircle, Info, Clock } from 'lucide-react';

const NotificationCenter = ({ notifications, onClear, onClearAll }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getIcon = (type) => {
    switch (type) {
      case 'decision': return <Brain className="w-4 h-4" />;
      case 'success': return <CheckCircle className="w-4 h-4" />;
      case 'warning': return <AlertCircle className="w-4 h-4" />;
      case 'info': return <Info className="w-4 h-4" />;
      case 'processing': return <Clock className="w-4 h-4" />;
      default: return <Info className="w-4 h-4" />;
    }
  };

  const getColor = (type) => {
    switch (type) {
      case 'decision': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'success': return 'bg-green-100 text-green-800 border-green-300';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'processing': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isOpen ? (
        <Button
          onClick={() => setIsOpen(true)}
          className="relative bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 shadow-lg"
          size="sm"
        >
          <Brain className="w-5 h-5" />
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      ) : (
        <Card className="w-96 max-h-[600px] shadow-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="w-5 h-5" />
              AI Agent Notifications
              {unreadCount > 0 && (
                <Badge className="bg-red-500">{unreadCount} new</Badge>
              )}
            </CardTitle>
            <div className="flex gap-2">
              {notifications.length > 0 && (
                <Button
                  onClick={onClearAll}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                >
                  Clear All
                </Button>
              )}
              <Button
                onClick={() => setIsOpen(false)}
                variant="ghost"
                size="sm"
                className="p-1"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[500px] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-6 text-center text-gray-500">
                  No notifications yet
                </div>
              ) : (
                <div className="space-y-2 p-2">
                  {notifications.map((notif, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border ${getColor(notif.type)} ${
                        !notif.read ? 'font-semibold' : ''
                      } cursor-pointer hover:shadow-md transition`}
                      onClick={() => onClear(idx)}
                    >
                      <div className="flex items-start gap-2">
                        <div className="mt-0.5">{getIcon(notif.type)}</div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium">{notif.agent || 'System'}</span>
                            <span className="text-xs opacity-70">
                              {new Date(notif.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <p className="text-sm">{notif.message}</p>
                          {notif.reasoning && (
                            <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs italic">
                              <strong>AI Reasoning:</strong> {notif.reasoning}
                            </div>
                          )}
                          {notif.details && (
                            <div className="mt-1 text-xs opacity-75">
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

