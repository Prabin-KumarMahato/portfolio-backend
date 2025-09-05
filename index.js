import express from 'express';
import cors from 'cors';
import { Resend } from 'resend';

// Initialize Express app
const app = express();

// Use your Vercel URL here
const vercelFrontendUrl = process.env.FRONTEND_URL || "https://prabinmahato.tech/";

// Setup CORS to allow requests only from your Vercel frontend
const corsOptions = {
    origin: vercelFrontendUrl,
};

app.use(cors(corsOptions));
app.use(express.json()); // Middleware to parse JSON bodies

// Initialize Resend with the API key from your Render environment variables
const resend = new Resend(process.env.RESEND_API_KEY);
const port = process.env.PORT || 3001;

// Define the API route for handling contact form submissions
app.post('/api/contact', async(req, res) => {
    try {
        // 1. Get the data from the request body
        const { name, email, message } = req.body;

        // Basic validation
        if (!name || !email || !message) {
            return res.status(400).json({ error: "Please fill all fields." });
        }

        // 2. Use Resend to send the email
        const { data, error } = await resend.emails.send({
            from: 'onboarding@resend.dev', // Resend's default email for getting started
            to: 'prabinkumarmahato54@gmail.com', // Your personal email address
            subject: `New Message from ${name} via Portfolio`,
            reply_to: email, // Set the sender's email as the reply-to address
            html: `
        <div>
          <h3>You have a new contact form submission:</h3>
          <p><strong>From:</strong> ${name}</p>
          <p><strong>Email:</strong> ${email}</p>
          <p><strong>Message:</strong></p>
          <p>${message}</p>
        </div>
      `,
        });

        // 3. Handle potential errors from Resend
        if (error) {
            console.error({ error });
            return res.status(400).json({ error: "Email could not be sent." });
        }

        // 4. Send a success response back to the frontend
        console.log('Email sent successfully:', { data });
        res.status(200).json({ message: "Message sent successfully!" });

    } catch (exception) {
        // Handle unexpected server errors
        console.error('Server exception:', exception);
        res.status(500).json({ error: "An internal server error occurred." });
    }
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});

export default app;