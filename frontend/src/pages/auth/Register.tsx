import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { apiClient } from '../../api/client';

export const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'buyer' | 'merchant'>('buyer');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/register', {
        name: name.trim() || 'User',
        email: email.trim(),
        password,
        role
      });
      localStorage.setItem('access_token', response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user_profile', JSON.stringify(response.data.user));
      }

      const userRole = response.data.user?.role || response.data.role;
      if (userRole === 'MERCHANT') {
        navigate('/dashboard');
      } else {
        localStorage.setItem('buyer_token', response.data.access_token);
        navigate('/buyer');
      }
    } catch (err: any) {
      const errData = err.response?.data;
      const validationErrors = errData?.error?.details?.errors || (Array.isArray(errData?.detail) ? errData.detail : null);
      let validationMsg: string | null = null;
      if (Array.isArray(validationErrors) && validationErrors.length > 0) {
        const first = validationErrors[0];
        const field = first?.loc?.slice(-1)[0];
        validationMsg = field ? `${field}: ${first?.msg}` : first?.msg;
      }

      setError(
        validationMsg ||
        errData?.error?.message ||
        (typeof errData?.detail === 'string' ? errData.detail : null) ||
        errData?.message ||
        (err.code === 'ERR_NETWORK' || !err.response
          ? 'Unable to connect to backend server. Please verify backend is running on port 8000.'
          : 'Registration failed. Please try again.')
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--rzp-bg)] p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-[var(--rzp-primary)] rounded-lg flex items-center justify-center mb-4">
            <span className="text-white font-bold text-2xl leading-none">G</span>
          </div>
          <CardTitle className="text-2xl">Create an Account</CardTitle>
          <p className="text-sm text-[var(--rzp-text-muted)] mt-2">
            Choose your account type to get started with GraahakLens
          </p>
        </CardHeader>
        <form onSubmit={handleRegister}>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-[var(--rzp-danger)] bg-[var(--rzp-danger-soft)] rounded-md border border-red-200">
                {error}
              </div>
            )}

            {/* Role Selection Tabs */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--rzp-text-muted)] uppercase tracking-wider">
                Account Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('buyer')}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    role === 'buyer'
                      ? 'border-[var(--rzp-primary)] bg-[var(--rzp-primary-soft)] text-[var(--rzp-primary)] ring-1 ring-[var(--rzp-primary)]'
                      : 'border-[var(--rzp-border)] bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-semibold text-sm">Buyer</div>
                  <div className="text-xs opacity-75 mt-0.5">Shop & Discover</div>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('merchant')}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    role === 'merchant'
                      ? 'border-[var(--rzp-primary)] bg-[var(--rzp-primary-soft)] text-[var(--rzp-primary)] ring-1 ring-[var(--rzp-primary)]'
                      : 'border-[var(--rzp-border)] bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-semibold text-sm">Merchant</div>
                  <div className="text-xs opacity-75 mt-0.5">Store & Intelligence</div>
                </button>
              </div>
            </div>

            <Input
              label="Full Name"
              type="text"
              placeholder={role === 'merchant' ? 'e.g. Rajesh Kumar' : 'e.g. Priya Sharma'}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <Input
              label="Email Address"
              type="email"
              placeholder={role === 'merchant' ? 'merchant@store.com' : 'buyer@example.com'}
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
              Create {role === 'merchant' ? 'Merchant' : 'Buyer'} Account
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
