import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

export interface MessageProps {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    isStreaming?: boolean;
}

export const ChatMessage: React.FC<{ message: MessageProps }> = ({ message }) => {
    const isUser = message.role === 'user';
    const content = message.content;

    // Detectar etiquetas de trazabilidad para renderizado especial
    const renderContent = () => {
        if (isUser) {
            return <Text style={styles.userText}>{content}</Text>;
        }

        // Dividir texto por posibles etiquetas de trazabilidad
        const tags = [
            { key: "[Conocimiento base de Lucil]", label: "🧠 Conocimiento Base", color: "#BB86FC" },
            { key: "[Documento propio:", label: "📄 Documento Propio", color: "#03DAC6" },
            { key: "[Búsqueda web pública:", label: "🌐 Web Pública", color: "#FFB74D" },
            { key: "[Inferencia / Deducción lógica]", label: "💡 Inferencia Lógica", color: "#64B5F6" }
        ];

        return (
            <View>
                <Text style={styles.assistantText}>
                    {content}
                    {message.isStreaming && <Text style={styles.cursor}> ▍</Text>}
                </Text>
            </View>
        );
    };

    return (
        <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
            <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
                {!isUser && (
                    <View style={styles.assistantHeader}>
                        <Text style={styles.avatarLabel}>✨ Lucil AI</Text>
                    </View>
                )}
                {renderContent()}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        marginVertical: 6,
        paddingHorizontal: 16,
        flexDirection: 'row',
        width: '100%',
    },
    userContainer: {
        justifyContent: 'flex-end',
    },
    assistantContainer: {
        justifyContent: 'flex-start',
    },
    bubble: {
        maxWidth: '85%',
        padding: 14,
        borderRadius: 18,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.2,
        shadowRadius: 2,
        elevation: 2,
    },
    userBubble: {
        backgroundColor: '#7C4DFF',
        borderBottomRightRadius: 4,
    },
    assistantBubble: {
        backgroundColor: '#1E1E2E',
        borderBottomLeftRadius: 4,
        borderWidth: 1,
        borderColor: '#2A2A3E',
    },
    assistantHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 6,
    },
    avatarLabel: {
        color: '#03DAC6',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 0.5,
    },
    userText: {
        color: '#FFFFFF',
        fontSize: 15,
        lineHeight: 22,
    },
    assistantText: {
        color: '#ECECF1',
        fontSize: 15,
        lineHeight: 24,
    },
    cursor: {
        color: '#03DAC6',
        fontWeight: 'bold',
    }
});