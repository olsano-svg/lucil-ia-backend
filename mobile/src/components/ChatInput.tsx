import React, { useState, useRef, useEffect } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, Text, Platform, ActivityIndicator } from 'react-native';
import { colors } from '../theme/colors';

interface ChatInputProps {
    onSend: (text: string, attachment?: { type: 'image' | 'document', file: any, name: string }) => void;
    onVoiceToggle?: (isRecording: boolean) => void;
    webSearchEnabled: boolean;
    onToggleWebSearch: () => void;
    disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
    onSend,
    onVoiceToggle,
    webSearchEnabled,
    onToggleWebSearch,
    disabled = false
}) => {
    const [text, setText] = useState('');
    const [isRecording, setIsRecording] = useState(false);
    const [attachment, setAttachment] = useState<{ type: 'image' | 'document', file: any, name: string } | null>(null);

    // Refs para estado fresco en listeners de eventos
    const textRef = useRef(text);
    textRef.current = text;

    const attachmentRef = useRef(attachment);
    attachmentRef.current = attachment;

    const disabledRef = useRef(disabled);
    disabledRef.current = disabled;

    const inputRef = useRef<any>(null);
    const recognitionRef = useRef<any>(null);

    // Refs para inputs de archivo web ocultos
    const docInputRef = useRef<any>(null);
    const imgInputRef = useRef<any>(null);

    const handleSend = () => {
        const currentText = textRef.current.trim();
        const currentAttach = attachmentRef.current;
        if ((currentText.length > 0 || currentAttach) && !disabledRef.current) {
            onSend(currentText, currentAttach || undefined);
            setText('');
            setAttachment(null);
            textRef.current = '';
            attachmentRef.current = null;
        }
    };

    // Listener nativo de teclado en Web para asegurar que Enter envíe el mensaje siempre
    useEffect(() => {
        if (Platform.OS === 'web') {
            const handleGlobalKeyDown = (e: KeyboardEvent) => {
                const target = e.target as HTMLElement;
                if (target && (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT')) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSend();
                    }
                }
            };
            window.addEventListener('keydown', handleGlobalKeyDown);
            return () => window.removeEventListener('keydown', handleGlobalKeyDown);
        }
    }, []);

    const toggleVoice = () => {
        if (Platform.OS === 'web') {
            const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (!SpeechRec) {
                if (onVoiceToggle) onVoiceToggle(!isRecording);
                setIsRecording(!isRecording);
                return;
            }

            if (isRecording) {
                if (recognitionRef.current) {
                    try { recognitionRef.current.stop(); } catch (e) {}
                }
                setIsRecording(false);
                if (onVoiceToggle) onVoiceToggle(false);
            } else {
                try {
                    const rec = new SpeechRec();
                    rec.lang = 'es-ES';
                    rec.continuous = true;
                    rec.interimResults = true;

                    rec.onstart = () => {
                        setIsRecording(true);
                        if (onVoiceToggle) onVoiceToggle(true);
                    };

                    rec.onresult = (event: any) => {
                        let transcript = '';
                        for (let i = 0; i < event.results.length; i++) {
                            transcript += event.results[i][0].transcript;
                        }
                        setText(transcript);
                        textRef.current = transcript;
                    };

                    rec.onerror = (err: any) => {
                        console.warn("Speech recognition error:", err);
                        setIsRecording(false);
                        if (onVoiceToggle) onVoiceToggle(false);
                    };

                    rec.onend = () => {
                        setIsRecording(false);
                        if (onVoiceToggle) onVoiceToggle(false);
                    };

                    rec.start();
                    recognitionRef.current = rec;
                } catch (e) {
                    console.error("Error iniciando reconocimiento de voz:", e);
                    setIsRecording(false);
                    if (onVoiceToggle) onVoiceToggle(false);
                }
            }
        } else {
            const nextState = !isRecording;
            setIsRecording(nextState);
            if (onVoiceToggle) onVoiceToggle(nextState);
        }
    };

    const handleDocClick = () => {
        if (Platform.OS === 'web' && docInputRef.current) {
            docInputRef.current.click();
        }
    };

    const handleImgClick = () => {
        if (Platform.OS === 'web' && imgInputRef.current) {
            imgInputRef.current.click();
        }
    };

    const handleFileChange = (e: any, type: 'document' | 'image') => {
        const file = e.target?.files?.[0];
        if (file) {
            setAttachment({
                type,
                file,
                name: file.name
            });
        }
    };

    return (
        <View style={styles.outerContainer}>
            {/* Inputs HTML invisibles para navegador Web */}
            {Platform.OS === 'web' && (
                <>
                    <input
                        type="file"
                        ref={docInputRef}
                        style={{ display: 'none' }}
                        accept=".pdf,.docx,.xlsx"
                        onChange={(e) => handleFileChange(e, 'document')}
                    />
                    <input
                        type="file"
                        ref={imgInputRef}
                        style={{ display: 'none' }}
                        accept="image/*"
                        onChange={(e) => handleFileChange(e, 'image')}
                    />
                </>
            )}

            {/* Vista previa de adjunto */}
            {attachment && (
                <View style={styles.attachmentBadge}>
                    <Text style={styles.attachmentText}>
                        {attachment.type === 'image' ? '🖼️ Imagen: ' : '📄 Documento: '}
                        {attachment.name}
                    </Text>
                    <TouchableOpacity onPress={() => setAttachment(null)} style={styles.removeBtn}>
                        <Text style={styles.removeBtnText}>✕</Text>
                    </TouchableOpacity>
                </View>
            )}

            <View style={styles.container}>
                {/* Botón Adjuntar Documento (PDF/Word/Excel) */}
                <TouchableOpacity
                    style={styles.iconButton}
                    onPress={handleDocClick}
                    disabled={disabled}
                    title="Adjuntar Documento (PDF, Word, Excel)"
                >
                    <Text style={styles.iconText}>📄</Text>
                </TouchableOpacity>

                {/* Botón Adjuntar Imagen */}
                <TouchableOpacity
                    style={styles.iconButton}
                    onPress={handleImgClick}
                    disabled={disabled}
                    title="Subir Imagen"
                >
                    <Text style={styles.iconText}>🖼️</Text>
                </TouchableOpacity>

                {/* Botón Búsqueda Web Toggle */}
                <TouchableOpacity
                    style={[styles.iconButton, webSearchEnabled && styles.webSearchActive]}
                    onPress={onToggleWebSearch}
                    title={webSearchEnabled ? "Búsqueda Web: Activa" : "Búsqueda Web: Desactivada"}
                >
                    <Text style={[styles.iconText, webSearchEnabled && styles.activeIconText]}>🌐</Text>
                </TouchableOpacity>

                {/* Campo de texto multilínea */}
                <TextInput
                    style={styles.input}
                    value={text}
                    onChangeText={(val) => {
                        setText(val);
                        textRef.current = val;
                    }}
                    placeholder={
                        isRecording 
                            ? "🎙️ Escuchando... habla ahora para dictar tu pregunta" 
                            : webSearchEnabled 
                                ? "Pregunta a Lucil con búsqueda web..." 
                                : "Pregunta a Lucil... (Presiona Enter para enviar)"
                    }
                    placeholderTextColor={colors.textSecondary}
                    multiline
                    editable={!disabled}
                    onKeyPress={(e: any) => {
                        if (Platform.OS === 'web') {
                            const key = e.nativeEvent?.key;
                            const shiftKey = e.nativeEvent?.shiftKey;
                            if (key === 'Enter' && !shiftKey) {
                                e.preventDefault?.();
                                handleSend();
                            }
                        }
                    }}
                    onSubmitEditing={(e) => {
                        if (Platform.OS === 'web' && !(e.nativeEvent as any)?.shiftKey) {
                            handleSend();
                        }
                    }}
                />

                {/* Micrófono o Enviar */}
                {text.trim().length === 0 && !attachment ? (
                    <TouchableOpacity
                        style={[styles.iconButton, isRecording && styles.recordingButton]}
                        onPress={toggleVoice}
                        disabled={disabled}
                        title={isRecording ? "Detener voz" : "Hablar con Lucil"}
                    >
                        <Text style={styles.iconText}>{isRecording ? '🛑' : '🎤'}</Text>
                    </TouchableOpacity>
                ) : (
                    <TouchableOpacity
                        style={[styles.sendButton, disabled && styles.disabledButton]}
                        onPress={handleSend}
                        disabled={disabled}
                    >
                        {disabled ? (
                            <ActivityIndicator size="small" color="#000" />
                        ) : (
                            <Text style={styles.sendText}>➤</Text>
                        )}
                    </TouchableOpacity>
                )}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    outerContainer: {
        backgroundColor: '#1E1E2E',
        borderTopWidth: 1,
        borderTopColor: '#2A2A3E',
        paddingHorizontal: 12,
        paddingVertical: 8,
    },
    attachmentBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#2A2A3E',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 12,
        marginBottom: 8,
        alignSelf: 'flex-start',
    },
    attachmentText: {
        color: '#03DAC6',
        fontSize: 13,
        fontWeight: '500',
    },
    removeBtn: {
        marginLeft: 8,
        padding: 2,
    },
    removeBtnText: {
        color: '#CF6679',
        fontSize: 14,
        fontWeight: 'bold',
    },
    container: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    iconButton: {
        padding: 8,
        borderRadius: 12,
        marginRight: 4,
    },
    iconText: {
        fontSize: 20,
    },
    webSearchActive: {
        backgroundColor: 'rgba(3, 218, 198, 0.2)',
        borderWidth: 1,
        borderColor: '#03DAC6',
    },
    activeIconText: {
        color: '#03DAC6',
    },
    recordingButton: {
        backgroundColor: 'rgba(207, 102, 121, 0.3)',
        borderRadius: 20,
        borderWidth: 1,
        borderColor: '#CF6679',
    },
    input: {
        flex: 1,
        backgroundColor: '#12121E',
        color: '#FFFFFF',
        borderRadius: 18,
        paddingHorizontal: 16,
        paddingTop: 10,
        paddingBottom: 10,
        fontSize: 15,
        maxHeight: 120,
        marginHorizontal: 6,
        borderWidth: 1,
        borderColor: '#2A2A3E',
    },
    sendButton: {
        backgroundColor: '#03DAC6',
        borderRadius: 18,
        width: 38,
        height: 38,
        justifyContent: 'center',
        alignItems: 'center',
    },
    disabledButton: {
        backgroundColor: '#4A4A5A',
    },
    sendText: {
        color: '#000',
        fontSize: 16,
        fontWeight: 'bold',
    }
});