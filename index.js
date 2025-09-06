import express from 'express';
import cors from 'cors';
import { Resend } from 'resend';

const app = express();
// Use your Vercel URL here
const vercelFrontendUrl = process.env.FRONTEND_URL || "https://prabinmahato.tech";

app.use(cors({ origin: vercelFrontendUrl }));
app.use(express.json());

const port = process.env.PORT || 3001;

// --- THIS CODE CHECKS FOR THE KEY AND GIVES A CLEAR ERROR ---
const resendApiKey = process.env.RESEND_API_KEY;

if (!resendApiKey) {
    console.error("FATAL ERROR: RESEND_API_KEY environment variable is NOT SET or NOT FOUND.");
}

const resend = new Resend(resendApiKey);
// ---

app.post('/api/contact', async(req, res) => {
    if (!resendApiKey) {
        return res.status(500).json({ error: "Server is not configured for sending emails." });
    }

    try {
        const { name, email, message } = req.body;

        console.log("Received form submission. Attempting to send email...");

        const { data, error } = await resend.emails.send({
            from: 'onboarding@resend.dev',
            to: 'prabinkumarmahato54@gmail.com',
            subject: `New Message from ${name} via Portfolio`,
            reply_to: email,
            html: `<p><strong>From:</strong> ${name} &lt;${email}&gt;</p><p><strong>Message:</strong> ${message}</p>`,
        });

        if (error) {
            console.error("Resend API Error:", error);
            return res.status(400).json({ error: "Email could not be sent due to an API error." });
        }

        console.log("Email sent successfully:", data);
        res.status(200).json({ message: "Message sent successfully!" });

    } catch (exception) {
        console.error("Server exception during email send:", exception);
        res.status(500).json({ error: "An internal server error occurred." });
    }
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});

export default app;