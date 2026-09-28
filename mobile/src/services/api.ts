import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || (
    Platform.OS === 'web' 
        ? (typeof window !== 'undefined' && window.location?.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
            ? 'https://lucil-ai-backend.onrender.com/api/v1' 
            : 'http://localhost:8081/api/v1')
        : 'http://192.168.68.100:8081/api/v1'
); 

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use(async (config) => {
    const token = await AsyncStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

export const authService = {
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await apiClient.post('/auth/login', formData.toString(), {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        if (response.data && response.data.access_token) {
            await AsyncStorage.setItem('token', response.data.access_token);
        }
        return response.data;
    },
    register: async (email: string, password: string) => {
        const response = await apiClient.post('/auth/register', { email, password });
        return response.data;
    },
    logout: async () => {
        await AsyncStorage.removeItem('token');
    },
    quickLogin: async () => {
        const defaultEmail = "admin";
        const defaultPass = "delarosa00";
        try {
            const res = await authService.login(defaultEmail, defaultPass);
            return res;
        } catch {
            await authService.register(defaultEmail, defaultPass);
            const res = await authService.login(defaultEmail, defaultPass);
            return res;
        }
    }
};

export const chatService = {
    listConversations: async () => {
        const response = await apiClient.get('/conversations/');
        return response.data;
    },
    getConversation: async (conversationId: string) => {
        const response = await apiClient.get(`/conversations/${conversationId}`);
        return response.data;
    },
    createConversation: async (title: string = "Nueva Conversación", projectId?: string) => {
        const response = await apiClient.post('/conversations/', {
            title,
            project_id: projectId
        });
        return response.data;
    },
    sendMessage: async (conversationId: string, content: string, role: string = 'user', enableWebSearch: boolean = false) => {
        const response = await apiClient.post(`/conversations/${conversationId}/messages`, {
            role,
            content,
            enable_web_search: enableWebSearch
        });
        return response.data;
    },
    streamMessage: async (
        conversationId: string,
        content: string,
        onChunk: (chunk: string) => void,
        onDone: () => void,
        onError: (err: any) => void,
        enableWebSearch: boolean = false
    ) => {
        const token = await AsyncStorage.getItem('token');
        const url = `${API_BASE_URL}/conversations/${conversationId}/stream`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                body: JSON.stringify({
                    role: 'user',
                    content: content,
                    enable_web_search: enableWebSearch
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            if (!response.body) {
                throw new Error("ReadableStream not supported in this environment");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (trimmed.startsWith("data: ")) {
                        const data = trimmed.slice(6);
                        if (data === "[DONE]") {
                            onDone();
                            return;
                        }
                        onChunk(data);
                    }
                }
            }
            onDone();
        } catch (err) {
            console.error("Error en streaming:", err);
            onError(err);
        }
    }
};

export const documentService = {
    uploadDocument: async (file: File | Blob, filename: string, projectId: string = "default") => {
        const formData = new FormData();
        formData.append('file', file, filename);

        const response = await apiClient.post(`/documents/${projectId}/upload`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        });
        return response.data;
    }
};

export const memoryService = {
    listMemories: async (category?: string) => {
        const params = category ? { category } : {};
        const response = await apiClient.get('/memories/', { params });
        return response.data;
    },
    createMemory: async (category: string, fact: string) => {
        const response = await apiClient.post('/memories/', { category, fact });
        return response.data;
    },
    deleteMemory: async (id: string) => {
        const response = await apiClient.delete(`/memories/${id}`);
        return response.data;
    }
};