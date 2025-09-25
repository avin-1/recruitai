
import { GoogleGenAI, Type } from "@google/genai";
import { EnhancedJobDescription } from '../types';

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  console.warn("API_KEY environment variable not set. Gemini API calls will fail.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY! });

const jobDescriptionSchema = {
  type: Type.OBJECT,
  properties: {
    enhancedTitle: {
      type: Type.STRING,
      description: "A more engaging and professional title for the job posting.",
    },
    engagingSummary: {
      type: Type.STRING,
      description: "A compelling 2-3 sentence summary of the role to attract top talent.",
    },
    keyResponsibilities: {
      type: Type.ARRAY,
      items: {
        type: Type.STRING,
      },
      description: "A list of 4-6 key responsibilities for the role, written in a clear and concise manner.",
    },
    requiredQualifications: {
      type: Type.ARRAY,
      items: {
        type: Type.STRING,
      },
      description: "A list of 4-6 essential qualifications and skills required for the role.",
    },
  },
  required: ["enhancedTitle", "engagingSummary", "keyResponsibilities", "requiredQualifications"],
};


export const enhanceJobDescription = async (jobTitle: string, rawDescription: string): Promise<EnhancedJobDescription | null> => {
  if (!API_KEY) {
    throw new Error("Gemini API key is not configured.");
  }
  try {
    const prompt = `
      You are an expert recruitment copywriter specializing in tech roles.
      Analyze the following job title and description, then rewrite it to be clear, engaging, and inclusive to attract a diverse pool of top talent.
      
      Job Title: "${jobTitle}"
      
      Job Description:
      "${rawDescription}"
      
      Return the output in the specified JSON format.
    `;
    
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: jobDescriptionSchema,
      },
    });

    const jsonText = response.text.trim();
    const parsedJson = JSON.parse(jsonText);

    return parsedJson as EnhancedJobDescription;

  } catch (error) {
    console.error("Error enhancing job description with Gemini:", error);
    return null;
  }
};
