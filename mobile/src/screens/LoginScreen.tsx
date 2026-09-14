import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService } from '../services/api';
import { colors } from '../theme/colors';

export const LoginScreen = ({ navigation }: any) => {
    const [email, setEmail] = useState('admin');
    const [password, setPassword] = useState('delarosa00');
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleAuth = async () => {
        if (!email || !password) {
            setErrorMessage('Por favor llena todos los campos');
            return;
        }
        
        setLoading(true);
        setErrorMessage(null);
        try {
            if (isLogin) {
                const res = await authService.login(email, password);
                await AsyncStorage.setItem('token', res.access_token);
                navigation.replace('Chat');
            } else {
                await authService.register(email, password);
                const res = await authService.login(email, password);
                await AsyncStorage.setItem('token', res.access_token);
                navigation.replace('Chat');
            }
        } catch (error: any) {
            console.error(error);
            const msg = error.response?.data?.detail || error.message || 'Error de conexión con el backend local';
            setErrorMessage(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleQuickLogin = async () => {
        setLoading(true);
        setErrorMessage(null);
        try {
            await authService.quickLogin();
            navigation.replace('Chat');
        } catch (error: any) {
            console.error(error);
            setErrorMessage('No se pudo conectar automáticamente con el servidor local');
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.card}>
                <View style={styles.statusBadge}>
                    <Text style={styles.statusDot}>●</Text>
                    <Text style={styles.statusText}>Backend Local Activo (Puerto 8000)</Text>
                </View>

                <Text style={styles.title}>✨ Lucil AI</Text>
                <Text style={styles.subtitle}>Asistente Personal 100% Local & Privado</Text>
                
                {errorMessage && (
                    <View style={styles.errorBox}>
                        <Text style={styles.errorText}>⚠️ {errorMessage}</Text>
                    </View>
                )}

                {/* Botón de Acceso Rápido */}
                <TouchableOpacity 
                    style={styles.quickButton} 
                    onPress={handleQuickLogin}
                    disabled={loading}
                >
                    <Text style={styles.quickButtonText}>⚡ Entrar como Administrador (1 Clic)</Text>
                </TouchableOpacity>

                <View style={styles.dividerRow}>
                    <View style={styles.dividerLine} />
                    <Text style={styles.dividerText}>o con tus credenciales</Text>
                    <View style={styles.dividerLine} />
                </View>

                <TextInput 
                    style={styles.input} 
                    placeholder="Email" 
                    placeholderTextColor={colors.textSecondary}
                    autoCapitalize="none"
                    value={email}
                    onChangeText={setEmail}
                />
                <TextInput 
                    style={styles.input} 
                    placeholder="Contraseña" 
                    placeholderTextColor={colors.textSecondary}
                    secureTextEntry
                    value={password}
                    onChangeText={setPassword}
                />
                
                <TouchableOpacity style={styles.button} onPress={handleAuth} disabled={loading}>
                    {loading ? (
                        <ActivityIndicator color="#000" />
                    ) : (
                        <Text style={styles.buttonText}>{isLogin ? 'Iniciar Sesión' : 'Crear Cuenta'}</Text>
                    )}
                </TouchableOpacity>
                
                <TouchableOpacity onPress={() => { setIsLogin(!isLogin); setErrorMessage(null); }}>
                    <Text style={styles.linkText}>
                        {isLogin ? '¿No tienes cuenta? Regístrate aquí' : '¿Ya tienes cuenta? Inicia sesión'}
                    </Text>
                </TouchableOpacity>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0E0E17',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    card: {
        width: '100%',
        maxWidth: 440,
        backgroundColor: '#1A1A27',
        borderRadius: 24,
        padding: 28,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        borderWidth: 1,
        borderColor: '#2D2D42',
    },
    statusBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        alignSelf: 'center',
        backgroundColor: 'rgba(3, 218, 198, 0.12)',
        paddingHorizontal: 12,
        paddingVertical: 5,
        borderRadius: 20,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: 'rgba(3, 218, 198, 0.3)',
    },
    statusDot: {
        color: '#03DAC6',
        fontSize: 10,
        marginRight: 6,
    },
    statusText: {
        color: '#03DAC6',
        fontSize: 12,
        fontWeight: '600',
    },
    title: {
        fontSize: 34,
        color: '#BB86FC',
        fontWeight: 'bold',
        textAlign: 'center',
        marginBottom: 6,
    },
    subtitle: {
        fontSize: 14,
        color: '#A0A0B8',
        textAlign: 'center',
        marginBottom: 24,
    },
    errorBox: {
        backgroundColor: 'rgba(207, 102, 121, 0.15)',
        padding: 10,
        borderRadius: 10,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: '#CF6679',
    },
    errorText: {
        color: '#CF6679',
        fontSize: 13,
        textAlign: 'center',
    },
    quickButton: {
        backgroundColor: '#03DAC6',
        paddingVertical: 14,
        borderRadius: 14,
        alignItems: 'center',
        marginBottom: 18,
    },
    quickButtonText: {
        color: '#000000',
        fontSize: 15,
        fontWeight: 'bold',
    },
    dividerRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 18,
    },
    dividerLine: {
        flex: 1,
        height: 1,
        backgroundColor: '#2D2D42',
    },
    dividerText: {
        color: '#6A6A85',
        fontSize: 12,
        marginHorizontal: 10,
    },
    input: {
        backgroundColor: '#12121E',
        color: '#FFFFFF',
        borderRadius: 14,
        paddingHorizontal: 16,
        paddingVertical: 14,
        marginBottom: 14,
        fontSize: 15,
        borderWidth: 1,
        borderColor: '#2D2D42',
    },
    button: {
        backgroundColor: '#7C4DFF',
        paddingVertical: 14,
        borderRadius: 14,
        alignItems: 'center',
        marginBottom: 18,
        marginTop: 4,
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    linkText: {
        color: '#03DAC6',
        textAlign: 'center',
        fontSize: 14,
    }
});