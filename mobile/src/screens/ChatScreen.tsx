import React, { useState, useEffect, useRef } from 'react';
import {
    SafeAreaView,
    FlatList,
    StyleSheet,
    KeyboardAvoidingView,
    Platform,
    View,
    Text,
    TouchableOpacity,
    Modal,
    TextInput,
    ActivityIndicator,
    Alert
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatMessage, MessageProps } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { colors } from '../theme/colors';
import { chatService, memoryService, documentService } from '../services/api';

export const ChatScreen = ({ navigation }: any) => {
    const [messages, setMessages] = useState<MessageProps[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [conversations, setConversations] = useState<any[]>([]);
    const [isThinking, setIsThinking] = useState(false);
    const [webSearchEnabled, setWebSearchEnabled] = useState(false);

    // Modales
    const [showHistory, setShowHistory] = useState(false);
    const [showMemory, setShowMemory] = useState(false);
    const [showVoiceLive, setShowVoiceLive] = useState(false);

    // Estado del Modo Voz Live en Tiempo Real
    const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
    const [liveUserText, setLiveUserText] = useState('');
    const [liveAssistantText, setLiveAssistantText] = useState('');
    const [isLiveActive, setIsLiveActive] = useState(false);

    const voiceRecognitionRef = useRef<any>(null);
    const isAssistantSpeakingRef = useRef(false);
    const voiceSilenceTimerRef = useRef<any>(null);
    const conversationIdRef = useRef(conversationId);
    conversationIdRef.current = conversationId;

    // Estado de memorias
    const [memories, setMemories] = useState<any[]>([]);
    const [newMemoryCategory, setNewMemoryCategory] = useState('preferencias');
    const [newMemoryFact, setNewMemoryFact] = useState('');
    const [loadingMemory, setLoadingMemory] = useState(false);

    // Notificaciones / Toasts
    const [toastMessage, setToastMessage] = useState<string | null>(null);

    const flatListRef = useRef<FlatList>(null);

    const showToast = (msg: string) => {
        setToastMessage(msg);
        setTimeout(() => setToastMessage(null), 4000);
    };

    // Cargar o crear conversación inicial
    useEffect(() => {
        const init = async () => {
            try {
                const list = await chatService.listConversations();
                setConversations(list);
                if (list.length > 0) {
                    await selectConversation(list[0].id);
                } else {
                    await handleNewChat();
                }
            } catch (err) {
                console.warn("Error cargando conversaciones iniciales, creando nueva:", err);
                await handleNewChat();
            }
        };
        init();
    }, []);

    const handleNewChat = async () => {
        try {
            const conv = await chatService.createConversation("Chat con Lucil");
            setConversationId(conv.id);
            setMessages([{
                id: 'welcome-1',
                role: 'assistant',
                content: '¡Hola! Soy Lucil AI, tu asistente personal 100% local, impulsada por Qwen 2.5 14B en tu GPU. ¿En qué trabajamos hoy?'
            }]);
            setShowHistory(false);
            const list = await chatService.listConversations();
            setConversations(list);
        } catch (err) {
            console.error("Error creando chat:", err);
        }
    };

    const selectConversation = async (id: string) => {
        try {
            setConversationId(id);
            setShowHistory(false);
            const conv = await chatService.getConversation(id);
            if (conv && conv.messages && conv.messages.length > 0) {
                setMessages(conv.messages.map((m: any) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content
                })));
            } else {
                setMessages([{
                    id: 'welcome-1',
                    role: 'assistant',
                    content: 'Conversación iniciada. ¿Qué consulta deseas realizar?'
                }]);
            }
        } catch (err) {
            console.error("Error seleccionando conversación:", err);
        }
    };

    // Enviar mensaje con streaming en tiempo real
    const handleSend = async (text: string, attachment?: { type: 'image' | 'document', file: any, name: string }) => {
        if (!conversationId) return;

        // Si hay un documento adjunto, subirlo primero a RAG
        if (attachment && attachment.type === 'document') {
            try {
                showToast(`Indexando documento "${attachment.name}" en ChromaDB...`);
                await documentService.uploadDocument(attachment.file, attachment.name);
                showToast(`✅ "${attachment.name}" indexado en la memoria de Lucil.`);
            } catch (err) {
                console.error("Error subiendo documento:", err);
                showToast(`❌ Error al indexar "${attachment.name}"`);
            }
        }

        const userMsgId = Date.now().toString();
        const newUserMsg: MessageProps = {
            id: userMsgId,
            role: 'user',
            content: attachment 
                ? `[Adjunto: ${attachment.name}]\n${text}`.trim() 
                : text
        };

        setMessages(prev => [...prev, newUserMsg]);
        setIsThinking(true);

        const assistantMsgId = (Date.now() + 1).toString();
        let streamAccumulator = "";

        // Si estamos en Web, usamos streaming SSE en vivo
        if (Platform.OS === 'web') {
            setMessages(prev => [
                ...prev,
                { id: assistantMsgId, role: 'assistant', content: '', isStreaming: true }
            ]);

            chatService.streamMessage(
                conversationId,
                text,
                (chunk) => {
                    setIsThinking(false);
                    streamAccumulator += chunk;
                    setMessages(prev =>
                        prev.map(msg =>
                            msg.id === assistantMsgId
                                ? { ...msg, content: streamAccumulator, isStreaming: true }
                                : msg
                        )
                    );
                },
                () => {
                    setIsThinking(false);
                    setMessages(prev =>
                        prev.map(msg =>
                            msg.id === assistantMsgId
                                ? { ...msg, isStreaming: false }
                                : msg
                        )
                    );
                },
                async (err) => {
                    console.warn("Fallo en streaming, recurriendo a mensaje tradicional:", err);
                    try {
                        const fallbackResp = await chatService.sendMessage(conversationId, text, 'user', webSearchEnabled);
                        setMessages(prev =>
                            prev.map(msg =>
                                msg.id === assistantMsgId
                                    ? { ...msg, content: fallbackResp.content, isStreaming: false }
                                    : msg
                            )
                        );
                    } catch (e) {
                        setMessages(prev =>
                            prev.map(msg =>
                                msg.id === assistantMsgId
                                    ? { ...msg, content: "Error al comunicar con Lucil AI.", isStreaming: false }
                                    : msg
                            )
                        );
                    } finally {
                        setIsThinking(false);
                    }
                },
                webSearchEnabled
            );
        } else {
            // Modo estándar móvil
            try {
                const response = await chatService.sendMessage(conversationId, text, 'user', webSearchEnabled);
                setMessages(prev => [
                    ...prev,
                    { id: response.id || assistantMsgId, role: 'assistant', content: response.content }
                ]);
            } catch (error) {
                console.error("Error al enviar mensaje", error);
            } finally {
                setIsThinking(false);
            }
        }
    };

    // Gestión de Memoria
    const loadMemories = async () => {
        setLoadingMemory(true);
        try {
            const data = await memoryService.listMemories();
            setMemories(data);
        } catch (err) {
            console.error("Error cargando memorias:", err);
        } finally {
            setLoadingMemory(false);
        }
    };

    const handleAddMemory = async () => {
        if (!newMemoryFact.trim()) return;
        try {
            await memoryService.createMemory(newMemoryCategory, newMemoryFact.trim());
            setNewMemoryFact('');
            await loadMemories();
            showToast("Recuerdo guardado en la memoria persistente de Lucil.");
        } catch (err) {
            console.error("Error creando memoria:", err);
        }
    };

    const handleDeleteMemory = async (id: string) => {
        try {
            await memoryService.deleteMemory(id);
            await loadMemories();
            showToast("Recuerdo eliminado de la memoria.");
    // --- LÓGICA DE VOZ EN TIEMPO REAL (LIVE VOICE CON INTERRUPCIÓN / BARGE-IN) ---
    const speakLive = (textToSpeak: string, onComplete?: () => void) => {
        if (typeof window === 'undefined' || !window.speechSynthesis) {
            if (onComplete) onComplete();
            return;
        }

        window.speechSynthesis.cancel();

        const cleanText = textToSpeak
            .replace(/\[Conocimiento base de Lucil\]/g, '')
            .replace(/\[Documento propio:.*?\]/g, '')
            .replace(/\[Búsqueda web pública:.*?\]/g, '')
            .replace(/\[Inferencia \/ Deducción lógica\]/g, '')
            .replace(/[\*\_#`]/g, '')
            .trim();

        if (!cleanText) {
            if (onComplete) onComplete();
            return;
        }

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'es-ES';
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        const voices = window.speechSynthesis.getVoices();
        const spanishVoice = voices.find(v => v.lang.startsWith('es') || v.name.toLowerCase().includes('spanish'));
        if (spanishVoice) {
            utterance.voice = spanishVoice;
        }

        utterance.onstart = () => {
            isAssistantSpeakingRef.current = true;
            setVoiceState('speaking');
        };

        utterance.onend = () => {
            isAssistantSpeakingRef.current = false;
            if (onComplete) onComplete();
        };

        utterance.onerror = () => {
            isAssistantSpeakingRef.current = false;
            if (onComplete) onComplete();
        };

        window.speechSynthesis.speak(utterance);
    };

    // Barge-in (Interrupción táctil o por voz)
    const handleBargeIn = () => {
        if (typeof window !== 'undefined' && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        isAssistantSpeakingRef.current = false;
        setVoiceState('listening');
        showToast("✋ Interrumpiste a Lucil. Habla nuevamente.");
        resumeListening();
    };

    const resumeListening = () => {
        if (voiceRecognitionRef.current) {
            try {
                voiceRecognitionRef.current.start();
            } catch (e) {
                // Ya estaba en ejecución
            }
        }
    };

    // Enviar pregunta por voz del usuario al cerebro de Lucil (Qwen 2.5 14B)
    const dispatchUserVoiceInput = async (spokenText: string) => {
        if (!spokenText.trim() || !conversationIdRef.current) return;

        setVoiceState('thinking');
        setLiveAssistantText('Pensando respuesta...');

        const cid = conversationIdRef.current;
        const userText = spokenText.trim();

        // Agregar al chat principal
        const userMsgId = Date.now().toString();
        setMessages(prev => [...prev, { id: userMsgId, role: 'user', content: userText }]);

        let accumulated = '';
        chatService.streamMessage(
            cid,
            userText,
            (chunk) => {
                accumulated += chunk;
                setLiveAssistantText(accumulated);
            },
            () => {
                // Agregar al chat principal
                setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), role: 'assistant', content: accumulated }]);
                // Hablar respuesta en voz alta
                speakLive(accumulated, () => {
                    // Al terminar, volver a escuchar
                    setLiveUserText('');
                    setVoiceState('listening');
                    resumeListening();
                });
            },
            (err) => {
                console.error("Error en respuesta de voz:", err);
                setLiveAssistantText("Hubo un problema al procesar la respuesta.");
                setVoiceState('listening');
                resumeListening();
            },
            webSearchEnabled
        );
    };

    // Iniciar llamada de voz interactiva
    const startLiveVoiceCall = () => {
        if (typeof window === 'undefined') return;
        const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRec) {
            alert("Tu navegador no soporta reconocimiento de voz en vivo. Por favor usa Google Chrome o Microsoft Edge.");
            return;
        }

        try {
            const rec = new SpeechRec();
            rec.lang = 'es-ES';
            rec.continuous = true;
            rec.interimResults = true;

            rec.onstart = () => {
                setIsLiveActive(true);
                setVoiceState('listening');
                setLiveUserText('');
                setLiveAssistantText('');
            };

            rec.onresult = (event: any) => {
                // Si Lucil estaba hablando y el usuario comenzó a hablar -> Barge-in automático!
                if (isAssistantSpeakingRef.current) {
                    handleBargeIn();
                }

                let interim = '';
                let final = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        final += event.results[i][0].transcript;
                    } else {
                        interim += event.results[i][0].transcript;
                    }
                }

                const currentSpoken = (final || interim).trim();
                if (currentSpoken) {
                    setLiveUserText(currentSpoken);

                    // Silencio de 1.4 segundos para emitir la pregunta
                    if (voiceSilenceTimerRef.current) {
                        clearTimeout(voiceSilenceTimerRef.current);
                    }

                    voiceSilenceTimerRef.current = setTimeout(() => {
                        try {
                            rec.stop();
                        } catch (e) {}
                        dispatchUserVoiceInput(currentSpoken);
                    }, 1400);
                }
            };

            rec.onerror = (err: any) => {
                console.warn("Live voice error:", err);
            };

            rec.onend = () => {
                // Si la llamada sigue activa y no está hablando el asistente, reiniciar escucha
                if (isLiveActive && !isAssistantSpeakingRef.current && voiceState === 'listening') {
                    try { rec.start(); } catch (e) {}
                }
            };

            rec.start();
            voiceRecognitionRef.current = rec;
            setIsLiveActive(true);
            setVoiceState('listening');
        } catch (err) {
            console.error("Error iniciando llamada de voz:", err);
            alert("No se pudo acceder al micrófono. Por favor permite los permisos de audio en tu navegador.");
        }
    };

    // Finalizar llamada de voz
    const stopLiveVoiceCall = () => {
        if (voiceSilenceTimerRef.current) {
            clearTimeout(voiceSilenceTimerRef.current);
        }
        if (voiceRecognitionRef.current) {
            try {
                voiceRecognitionRef.current.abort();
            } catch (e) {}
            voiceRecognitionRef.current = null;
        }
        if (typeof window !== 'undefined' && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        isAssistantSpeakingRef.current = false;
        setIsLiveActive(false);
        setVoiceState('idle');
        setLiveUserText('');
        setLiveAssistantText('');
        setShowVoiceLive(false);
    };

    return (
        <SafeAreaView style={styles.container}>
            {/* Header Superior */}
            <View style={styles.header}>
                <TouchableOpacity
                    style={styles.headerButton}
                    onPress={() => { setShowHistory(true); chatService.listConversations().then(setConversations); }}
                >
                    <Text style={styles.headerButtonText}>📜 Chats</Text>
                </TouchableOpacity>

                <View style={styles.headerCenter}>
                    <Text style={styles.headerTitle}>Lucil AI</Text>
                    <View style={styles.modelBadge}>
                        <Text style={styles.modelDot}>●</Text>
                        <Text style={styles.modelText}>Qwen 2.5 14B Local</Text>
                    </View>
                </View>

                <View style={styles.headerRight}>
                    <TouchableOpacity
                        style={styles.headerButton}
                        onPress={() => { setShowMemory(true); loadMemories(); }}
                    >
                        <Text style={styles.headerButtonText}>🧠 Memoria</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={styles.headerButton}
                        onPress={() => setShowVoiceLive(true)}
                    >
                        <Text style={styles.headerButtonText}>🎙️ Voz</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Toast Flotante */}
            {toastMessage && (
                <View style={styles.toastBanner}>
                    <Text style={styles.toastText}>{toastMessage}</Text>
                </View>
            )}

            {/* Área de Chat */}
            <KeyboardAvoidingView
                style={styles.keyboardAvoiding}
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            >
                <FlatList
                    ref={flatListRef}
                    data={messages}
                    keyExtractor={item => item.id}
                    renderItem={({ item }) => <ChatMessage message={item} />}
                    contentContainerStyle={styles.listContent}
                    onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
                />

                {/* Indicador de pensamiento */}
                {isThinking && (
                    <View style={styles.thinkingContainer}>
                        <ActivityIndicator size="small" color="#03DAC6" />
                        <Text style={styles.thinkingText}>Lucil está analizando...</Text>
                    </View>
                )}

                {/* Input de Chat */}
                <ChatInput
                    onSend={handleSend}
                    onVoiceToggle={() => setShowVoiceLive(true)}
                    webSearchEnabled={webSearchEnabled}
                    onToggleWebSearch={() => {
                        const next = !webSearchEnabled;
                        setWebSearchEnabled(next);
                        showToast(next ? "🌐 Búsqueda web pública activada" : "🌐 Búsqueda web desactivada");
                    }}
                    disabled={isThinking}
                />
            </KeyboardAvoidingView>

            {/* MODAL: HISTORIAL DE CONVERSACIONES */}
            <Modal visible={showHistory} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalCard}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>📜 Historial de Chats</Text>
                            <TouchableOpacity onPress={() => setShowHistory(false)}>
                                <Text style={styles.closeBtn}>✕</Text>
                            </TouchableOpacity>
                        </View>

                        <TouchableOpacity style={styles.newChatBtn} onPress={handleNewChat}>
                            <Text style={styles.newChatBtnText}>+ Nueva Conversación</Text>
                        </TouchableOpacity>

                        <FlatList
                            data={conversations}
                            keyExtractor={item => item.id}
                            renderItem={({ item }) => (
                                <TouchableOpacity
                                    style={[
                                        styles.historyItem,
                                        item.id === conversationId && styles.historyItemActive
                                    ]}
                                    onPress={() => selectConversation(item.id)}
                                >
                                    <Text style={styles.historyItemText}>
                                        {item.title || "Conversación sin título"}
                                    </Text>
                                    <Text style={styles.historyItemDate}>
                                        {new Date(item.created_at).toLocaleDateString()}
                                    </Text>
                                </TouchableOpacity>
                            )}
                        />
                    </View>
                </View>
            </Modal>

            {/* MODAL: GESTOR DE MEMORIAS (CRUD) */}
            <Modal visible={showMemory} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalCard}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>🧠 Memoria Persistente de Lucil</Text>
                            <TouchableOpacity onPress={() => setShowMemory(false)}>
                                <Text style={styles.closeBtn}>✕</Text>
                            </TouchableOpacity>
                        </View>
                        <Text style={styles.modalSubtitle}>
                            Datos y preferencias que Lucil recuerda activamente en cada conversación.
                        </Text>

                        {/* Formulario nuevo recuerdo */}
                        <View style={styles.newMemoryRow}>
                            <TextInput
                                style={styles.memoryInput}
                                placeholder="Ej: Soy alérgico a la aspirina / Mi proyecto es X..."
                                placeholderTextColor="#888"
                                value={newMemoryFact}
                                onChangeText={setNewMemoryFact}
                            />
                            <TouchableOpacity style={styles.addMemoryBtn} onPress={handleAddMemory}>
                                <Text style={styles.addMemoryBtnText}>Guardar</Text>
                            </TouchableOpacity>
                        </View>

                        {loadingMemory ? (
                            <ActivityIndicator color="#03DAC6" style={{ marginVertical: 20 }} />
                        ) : (
                            <FlatList
                                data={memories}
                                keyExtractor={item => item.id}
                                ListEmptyComponent={
                                    <Text style={styles.emptyText}>No hay recuerdos registrados aún.</Text>
                                }
                                renderItem={({ item }) => (
                                    <View style={styles.memoryItem}>
                                        <View style={{ flex: 1 }}>
                                            <Text style={styles.memoryCategory}>[{item.category || "general"}]</Text>
                                            <Text style={styles.memoryFact}>{item.fact}</Text>
                                        </View>
                                        <TouchableOpacity
                                            style={styles.deleteMemoryBtn}
                                            onPress={() => handleDeleteMemory(item.id)}
                                        >
                                            <Text style={styles.deleteMemoryText}>🗑️</Text>
                                        </TouchableOpacity>
                                    </View>
                                )}
                            />
                        )}
                    </View>
                </View>
            </Modal>

            {/* MODAL: MODO VOZ EN TIEMPO REAL */}
            <Modal visible={showVoiceLive} animationType="fade" transparent>
                <View style={styles.modalOverlay}>
                    <View style={[styles.modalCard, { alignItems: 'center', paddingVertical: 28 }]}>
                        <Text style={styles.voiceTitle}>🎙️ Lucil Live Voice</Text>
                        <Text style={styles.voiceSubtitle}>Conversación por voz continua en tiempo real con Qwen 2.5 14B</Text>

                        {/* ESTADO IDLE / INICIAL: BOTÓN CLARO PARA ACTIVAR */}
                        {voiceState === 'idle' && (
                            <View style={{ alignItems: 'center', width: '100%', marginVertical: 12 }}>
                                <TouchableOpacity 
                                    style={styles.startCallButton} 
                                    onPress={startLiveVoiceCall}
                                    activeOpacity={0.8}
                                >
                                    <View style={styles.pulseCircleIdle}>
                                        <Text style={{ fontSize: 44 }}>🎙️</Text>
                                    </View>
                                    <Text style={styles.startCallButtonText}>▶️ Conectar Micrófono e Iniciar Conversación</Text>
                                    <Text style={styles.startCallButtonSubtext}>Habla libremente con Lucil en tiempo real y con interrupción (Barge-in)</Text>
                                </TouchableOpacity>
                            </View>
                        )}

                        {/* ESTADO ESCUCHANDO */}
                        {voiceState === 'listening' && (
                            <View style={{ alignItems: 'center', width: '100%', marginVertical: 8 }}>
                                <View style={[styles.pulseCircle, styles.circleListening]}>
                                    <Text style={{ fontSize: 48 }}>🎧</Text>
                                </View>
                                <Text style={styles.liveListeningLabel}>🟢 Te escucho atentamente...</Text>
                                <Text style={styles.liveListeningHint}>Habla con libertad. Lucil procesará tu voz al terminar cada frase.</Text>
                                {liveUserText ? (
                                    <View style={styles.liveTranscriptCard}>
                                        <Text style={styles.transcriptTag}>Tú dijiste:</Text>
                                        <Text style={styles.transcriptText}>"{liveUserText}"</Text>
                                    </View>
                                ) : null}
                            </View>
                        )}

                        {/* ESTADO PENSANDO */}
                        {voiceState === 'thinking' && (
                            <View style={{ alignItems: 'center', width: '100%', marginVertical: 8 }}>
                                <View style={[styles.pulseCircle, styles.circleThinking]}>
                                    <ActivityIndicator size="large" color="#BB86FC" />
                                </View>
                                <Text style={styles.liveThinkingLabel}>⚡ Lucil está pensando...</Text>
                                <Text style={styles.liveListeningHint}>Generando respuesta con Qwen 2.5 14B en GPU local</Text>
                            </View>
                        )}

                        {/* ESTADO HABLANDO */}
                        {voiceState === 'speaking' && (
                            <View style={{ alignItems: 'center', width: '100%', marginVertical: 8 }}>
                                <View style={[styles.pulseCircle, styles.circleSpeaking]}>
                                    <Text style={{ fontSize: 48 }}>🔊</Text>
                                </View>
                                <Text style={styles.liveSpeakingLabel}>🗣️ Lucil está hablando...</Text>
                                {liveAssistantText ? (
                                    <View style={styles.liveTranscriptCard}>
                                        <Text style={styles.transcriptTagLucil}>Lucil:</Text>
                                        <Text style={styles.transcriptText}>{liveAssistantText}</Text>
                                    </View>
                                ) : null}

                                {/* BOTÓN DE INTERRUPCIÓN (BARGE-IN) */}
                                <TouchableOpacity 
                                    style={styles.bargeInBtn} 
                                    onPress={handleBargeIn}
                                    activeOpacity={0.8}
                                >
                                    <Text style={styles.bargeInText}>🛑 Interrumpir a Lucil (Barge-in)</Text>
                                </TouchableOpacity>
                            </View>
                        )}

                        {/* BOTÓN FINALIZAR LLAMADA */}
                        <TouchableOpacity
                            style={styles.closeVoiceBtn}
                            onPress={stopLiveVoiceCall}
                        >
                            <Text style={styles.closeVoiceText}>Finalizar Llamada de Voz</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </Modal>
        </SafeAreaView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0E0E17',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: '#161622',
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A3E',
    },
    headerButton: {
        backgroundColor: '#2A2A3E',
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 8,
        marginHorizontal: 2,
    },
    headerButtonText: {
        color: '#FFFFFF',
        fontSize: 13,
        fontWeight: '600',
    },
    headerCenter: {
        alignItems: 'center',
    },
    headerTitle: {
        color: '#BB86FC',
        fontSize: 18,
        fontWeight: 'bold',
    },
    modelBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        marginTop: 2,
    },
    modelDot: {
        color: '#03DAC6',
        fontSize: 10,
        marginRight: 4,
    },
    modelText: {
        color: '#03DAC6',
        fontSize: 11,
        fontWeight: '500',
    },
    headerRight: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    toastBanner: {
        backgroundColor: '#2A2A3E',
        padding: 8,
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#03DAC6',
    },
    toastText: {
        color: '#03DAC6',
        fontSize: 13,
        fontWeight: '500',
    },
    keyboardAvoiding: {
        flex: 1,
    },
    listContent: {
        paddingVertical: 12,
    },
    thinkingContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingVertical: 8,
    },
    thinkingText: {
        color: '#03DAC6',
        fontSize: 13,
        marginLeft: 8,
        fontStyle: 'italic',
    },
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.7)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    modalCard: {
        width: '100%',
        maxWidth: 520,
        maxHeight: '85%',
        backgroundColor: '#1A1A27',
        borderRadius: 20,
        padding: 24,
        borderWidth: 1,
        borderColor: '#2D2D42',
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    modalTitle: {
        color: '#FFFFFF',
        fontSize: 20,
        fontWeight: 'bold',
    },
    modalSubtitle: {
        color: '#A0A0B8',
        fontSize: 13,
        marginBottom: 16,
    },
    closeBtn: {
        color: '#CF6679',
        fontSize: 22,
        fontWeight: 'bold',
        padding: 4,
    },
    newChatBtn: {
        backgroundColor: '#7C4DFF',
        paddingVertical: 12,
        borderRadius: 12,
        alignItems: 'center',
        marginBottom: 16,
    },
    newChatBtnText: {
        color: '#FFFFFF',
        fontWeight: 'bold',
        fontSize: 14,
    },
    historyItem: {
        backgroundColor: '#12121E',
        padding: 14,
        borderRadius: 12,
        marginBottom: 8,
        borderWidth: 1,
        borderColor: '#2A2A3E',
    },
    historyItemActive: {
        borderColor: '#03DAC6',
        backgroundColor: 'rgba(3, 218, 198, 0.08)',
    },
    historyItemText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '600',
    },
    historyItemDate: {
        color: '#888',
        fontSize: 11,
        marginTop: 4,
    },
    newMemoryRow: {
        flexDirection: 'row',
        marginBottom: 16,
    },
    memoryInput: {
        flex: 1,
        backgroundColor: '#12121E',
        color: '#FFF',
        borderRadius: 10,
        paddingHorizontal: 14,
        fontSize: 14,
        borderWidth: 1,
        borderColor: '#2D2D42',
        marginRight: 8,
    },
    addMemoryBtn: {
        backgroundColor: '#03DAC6',
        justifyContent: 'center',
        paddingHorizontal: 16,
        borderRadius: 10,
    },
    addMemoryBtnText: {
        color: '#000',
        fontWeight: 'bold',
        fontSize: 14,
    },
    memoryItem: {
        flexDirection: 'row',
        backgroundColor: '#12121E',
        padding: 12,
        borderRadius: 10,
        marginBottom: 8,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#2D2D42',
    },
    memoryCategory: {
        color: '#BB86FC',
        fontSize: 12,
        fontWeight: 'bold',
        marginBottom: 2,
    },
    memoryFact: {
        color: '#ECECF1',
        fontSize: 14,
    },
    deleteMemoryBtn: {
        padding: 8,
    },
    deleteMemoryText: {
        fontSize: 16,
    },
    emptyText: {
        color: '#888',
        textAlign: 'center',
        marginVertical: 20,
    },
    voiceTitle: {
        color: '#BB86FC',
        fontSize: 22,
        fontWeight: 'bold',
        marginBottom: 6,
    },
    voiceSubtitle: {
        color: '#A0A0B8',
        fontSize: 14,
        marginBottom: 16,
        textAlign: 'center',
    },
    startCallButton: {
        alignItems: 'center',
        backgroundColor: '#1E1E2E',
        borderRadius: 20,
        padding: 24,
        borderWidth: 2,
        borderColor: '#03DAC6',
        width: '100%',
        cursor: 'pointer',
    },
    pulseCircleIdle: {
        width: 90,
        height: 90,
        borderRadius: 45,
        backgroundColor: 'rgba(3, 218, 198, 0.2)',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 14,
        borderWidth: 2,
        borderColor: '#03DAC6',
    },
    startCallButtonText: {
        color: '#03DAC6',
        fontSize: 16,
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 6,
    },
    startCallButtonSubtext: {
        color: '#A0A0B8',
        fontSize: 13,
        textAlign: 'center',
    },
    pulseCircle: {
        width: 110,
        height: 110,
        borderRadius: 55,
        backgroundColor: 'rgba(3, 218, 198, 0.15)',
        borderWidth: 2,
        borderColor: '#03DAC6',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 16,
    },
    circleListening: {
        backgroundColor: 'rgba(3, 218, 198, 0.25)',
        borderColor: '#03DAC6',
    },
    circleThinking: {
        backgroundColor: 'rgba(187, 134, 252, 0.25)',
        borderColor: '#BB86FC',
    },
    circleSpeaking: {
        backgroundColor: 'rgba(255, 183, 77, 0.25)',
        borderColor: '#FFB74D',
    },
    liveListeningLabel: {
        color: '#03DAC6',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    liveThinkingLabel: {
        color: '#BB86FC',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    liveSpeakingLabel: {
        color: '#FFB74D',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    liveListeningHint: {
        color: '#A0A0B8',
        fontSize: 13,
        textAlign: 'center',
        marginBottom: 12,
    },
    liveTranscriptCard: {
        backgroundColor: '#12121E',
        borderRadius: 14,
        padding: 14,
        width: '100%',
        marginVertical: 10,
        borderWidth: 1,
        borderColor: '#2D2D42',
    },
    transcriptTag: {
        color: '#03DAC6',
        fontSize: 11,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    transcriptTagLucil: {
        color: '#BB86FC',
        fontSize: 11,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    transcriptText: {
        color: '#FFFFFF',
        fontSize: 14,
        lineHeight: 22,
    },
    bargeInBtn: {
        backgroundColor: '#CF6679',
        paddingHorizontal: 24,
        paddingVertical: 12,
        borderRadius: 14,
        marginTop: 10,
        marginBottom: 8,
        width: '100%',
        alignItems: 'center',
        cursor: 'pointer',
    },
    bargeInText: {
        color: '#000000',
        fontWeight: 'bold',
        fontSize: 15,
    },
    closeVoiceBtn: {
        backgroundColor: '#2A2A3E',
        paddingHorizontal: 24,
        paddingVertical: 12,
        borderRadius: 14,
        marginTop: 14,
        width: '100%',
        alignItems: 'center',
    },
    closeVoiceText: {
        color: '#CF6679',
        fontSize: 14,
        fontWeight: 'bold',
    }
});