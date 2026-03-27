import React, { useState } from 'react';
import { Container, Typography, Box, TextField, Button, Alert, CircularProgress } from '@mui/material';
import { apiRequest } from '../utils/apiRequest';

const ContactPage = () => {
  const [form, setForm] = useState({ name: '', email: '', message: '' });
  const [status, setStatus] = useState(null); // 'success' | 'error'
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);
    try {
      await apiRequest('/contact/', 'POST', form);
      setStatus('success');
      setForm({ name: '', email: '', message: '' });
    } catch (error) {
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4, mb: 8 }}>
      <Typography variant="h4" gutterBottom>Contact Us</Typography>
      {status === 'success' && <Alert severity="success" sx={{ mb: 2 }}>Your message has been received. We'll get back to you soon!</Alert>}
      {status === 'error' && <Alert severity="error" sx={{ mb: 2 }}>Failed to send message. Please try again.</Alert>}
      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField label="Name" name="name" value={form.name} onChange={handleChange} required />
        <TextField label="Email" name="email" type="email" value={form.email} onChange={handleChange} required />
        <TextField label="Message" name="message" multiline rows={4} value={form.message} onChange={handleChange} required />
        <Button type="submit" variant="contained" disabled={loading} sx={{ alignSelf: 'flex-start' }}>
          {loading ? <CircularProgress size={20} color="inherit" /> : 'Send Message'}
        </Button>
      </Box>
    </Container>
  );
};

export default ContactPage;

