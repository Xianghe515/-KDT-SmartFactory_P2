import { v4 as uuidv4 } from 'uuid'; // 파일 이름 생성을 위해 uuidv4 임포트

export class FileUtil {
    // 기존 코드 유지
    public static loadImageBase64(fileData: File): Promise<string | ArrayBuffer> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(fileData);
            reader.onload = () => resolve(reader.result);
            reader.onerror = (error) => reject(error);
        });
    }

    public static loadImage(fileData: File): Promise<HTMLImageElement> {
        return new Promise((resolve, reject) => {
            const url = URL.createObjectURL(fileData);
            const image = new Image();
            image.src = url;
            image.onload = () => resolve(image);
            image.onerror = reject;
        });
    }

    public static loadImages(fileData: File[]): Promise<HTMLImageElement[]> {
        return new Promise((resolve, reject) => {
            const promises: Promise<HTMLImageElement>[] = fileData.map((data: File) => FileUtil.loadImage(data));
            Promise
                .all(promises)
                .then((values: HTMLImageElement[]) => resolve(values))
                .catch((error) => reject(error));
        });
    }

    public static readFile(fileData: File): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = (event: any) => {
                resolve(event?.target?.result);
            };
            reader.onerror = reject;
            reader.readAsText(fileData);
        });
    }

    public static readFiles(fileData: File[]): Promise<string[]> {
        return new Promise((resolve, reject) => {
            const promises: Promise<string>[] = fileData.map((data: File) => FileUtil.readFile(data));
            Promise
                .all(promises)
                .then((values: string[]) => resolve(values))
                .catch((error) => reject(error));
        });
    }

    public static extractFileExtension(name: string): string | null {
        const parts = name.split('.');
        return parts.length > 1 ? parts[parts.length - 1] : null;
    }

    public static extractFileName(name: string): string | null {
        const splitPath = name.split('.');
        let fName = '';
        for (const idx of Array(splitPath.length - 1).keys()) {
            if (fName === '') fName += splitPath[idx];
            else fName += '.' + splitPath[idx];
        }
        return fName;
    }

    // --- 추가된 코드: URL로부터 File 객체 생성 함수 ---
    public static async createFileFromUrl(imageUrl: string, suggestedFileName?: string): Promise<File | null> {
        try {
            console.log(`Attempting to fetch image from URL: ${imageUrl}`);
            const response = await fetch(imageUrl); // URL에서 데이터 비동기적으로 가져오기

            if (!response.ok) {
                console.error(`HTTP error! status: ${response.status} when fetching ${imageUrl}`);
                return null; // HTTP 오류 발생 시 null 반환
            }

            const blob = await response.blob(); // 데이터를 Blob 형태로 얻기

            // 파일 이름 및 타입 결정
            let fileName = suggestedFileName;
            if (!fileName) {
                 // URL에서 파일 이름 추정 시 슬래시 / 뒤의 마지막 부분을 사용
                const urlParts = imageUrl.split('/');
                fileName = urlParts[urlParts.length - 1] || `downloaded_image_${uuidv4()}`; // URL에 이름이 없으면 고유 ID 사용
                 // 확장자가 없는 경우 .jpg 등을 붙여줄 수도 있습니다. (선택 사항)
                if (!FileUtil.extractFileExtension(fileName) && blob.type && blob.type.startsWith('image/')) {
                     const mimeExtension = blob.type.split('/')[1];
                     fileName = `${fileName}.${mimeExtension}`;
                }
            }

            const mimeType = blob.type || 'image/jpeg'; // Blob에 타입 정보가 없으면 기본값 사용

            // Blob으로부터 File 객체 생성
            const file = new File([blob], fileName, { type: mimeType });

            console.log(`Successfully created File object: ${file.name} (${file.type})`);
            return file; // 생성된 File 객체 반환

        } catch (error) {
            console.error(`Exception while creating File from URL ${imageUrl}:`, error);
            return null; // 예외 발생 시 null 반환
        }
    }
    // --------------------------------------------------
}