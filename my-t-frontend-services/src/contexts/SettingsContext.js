import React, { createContext, useContext, useState, useEffect } from 'react';

const SettingsContext = createContext();

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error('useSettings must be used within a SettingsProvider');
    }
    return context;
};

export const SettingsProvider = ({ children }) => {
    const [settings, setSettings] = useState({
        model: 'gpt-4o',
        theme: 'light', // 'light' or 'dark'
        streamingMode: 'traditional', // 'traditional' | 'streaming'
        showRightSidebar: true // true | false
    });

    // Load settings from localStorage on mount
    useEffect(() => {
        const savedSettings = localStorage.getItem('userSettings');
        if (savedSettings) {
            try {
                const parsedSettings = JSON.parse(savedSettings);
                // Migrate legacy value 'regular' -> 'traditional'
                if (parsedSettings.streamingMode === 'regular') {
                    parsedSettings.streamingMode = 'traditional';
                }
                setSettings(prev => ({ ...prev, ...parsedSettings }));
            } catch (error) {
                console.error('Error parsing saved settings:', error);
            }
        }
    }, []);

    // Save settings to localStorage whenever they change
    useEffect(() => {
        localStorage.setItem('userSettings', JSON.stringify(settings));
    }, [settings]);

    const updateSettings = (newSettings) => {
        setSettings(prev => ({ ...prev, ...newSettings }));
    };

    const value = {
        settings,
        updateSettings
    };

    return (
        <SettingsContext.Provider value={value}>
            {children}
        </SettingsContext.Provider>
    );
}; 