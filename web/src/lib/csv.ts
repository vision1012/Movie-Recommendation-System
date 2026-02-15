import fs from 'fs';
import Papa from 'papaparse';

export async function parseCsv<T>(filePath: string): Promise<T[]> {
    const fileContent = fs.readFileSync(filePath, 'utf8');
    return new Promise((resolve, reject) => {
        Papa.parse<T>(fileContent, {
            header: true,
            dynamicTyping: true,
            skipEmptyLines: true,
            complete: (results) => {
                if (results.errors.length > 0) {
                    console.warn(`CSV parsing warnings for ${filePath}:`, results.errors);
                }
                resolve(results.data);
            },
            error: (error: Error) => {
                reject(error);
            },
        });
    });
}
