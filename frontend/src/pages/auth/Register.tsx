import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { apiClient } from '../../api/client';

export const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/register', { 
        email, 
        password,
        role: 'MERCHANT'
      });
      localStorage.setItem('access_token', response.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--rzp-bg)] p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-[var(--rzp-primary)] rounded-lg flex items-center justify-center mb-4">
            <span className="text-white font-bold text-2xl leading-none">R</span>
          </div>
          <CardTitle className="text-2xl">Create an account</CardTitle>
          <p className="text-sm text-[var(--rzp-text-muted)] mt-2">
            Start optimizing with AI Commerce
          </p>
        </CardHeader>
        <form onSubmit={handleRegister}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-[var(--rzp-danger)] bg-[var(--rzp-danger-soft)] rounded-md border border-red-200">
                {error}
              </div>
            )}
            <Input
              label="Email"
              type="email"
              placeholder="merchant@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </CardContent>
          <CardFooter className="flex flex-col space-y-4 pt-4">
            <Button type="submit" className="w-full" isLoading={loading}>
              Create Account
            </Button>
            <div className="text-center text-sm text-[var(--rzp-text-muted)]">
              Already have an account?{' '}
              <Link to="/login" className="text-[var(--rzp-primary)] hover:underline font-medium">
                Sign in
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};
