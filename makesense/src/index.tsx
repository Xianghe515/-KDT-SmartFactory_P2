import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.scss';
import App from './App';
import configureStore from './configureStore';
import { Provider } from 'react-redux';
import { AppInitializer } from './logic/initializer/AppInitializer';

// Makesense 내부의 필요한 함수들을 임포트합니다.
// utils/ImageDataUtil.ts 파일에서 createImageDataFromFileData 함수를 가져옵니다.
import { ImageDataUtil } from './utils/ImageDataUtil';
// store/labels/actionCreators.ts 파일에서 addImageData 및 updateActiveImageIndex 액션 생성 함수를 가져옵니다.
import { addImageData, updateActiveImageIndex } from './store/labels/actionCreators';
// utils/FileUtil.ts 파일에서 수정/추가한 FileUtil 클래스를 가져옵니다.
import { FileUtil } from './utils/FileUtil';
// store/general/actionCreators.ts 파일에서 updateProjectData 액션 생성 함수를 가져옵니다.
import { updateProjectData } from './store/general/actionCreators';
// data/enums/ProjectType.ts 파일에서 ProjectType enum을 가져옵니다.
import { ProjectType } from './data/enums/ProjectType';
// data/enums/PopupWindowType.ts 파일에서 PopupWindowType enum을 가져옵니다.
// import { PopupWindowType } from './data/enums/PopupWindowType'; // 라벨 이름 팝업 처리가 필요하다면 임포트


export const store = configureStore();

// --- 이 부분에 URL 파라미터 처리 및 이미지 로딩 트리거 로직 추가 ---
const params = new URLSearchParams(window.location.search);
const imageUrl = params.get('image_url'); // Flask에서 보낸 파라미터 이름 ('image_url'로 가정)

// 비동기 로딩 프로세스를 관리하기 위한 즉시 실행 함수 (IIFE)
(async () => {
    if (imageUrl) {
        console.log(`Detected image_url parameter: ${imageUrl}. Attempting to load image.`);

        try {
            // URL에서 File 객체 생성 비동기 호출
            const file = await FileUtil.createFileFromUrl(imageUrl);

            if (file) {
                console.log("Successfully created File object from URL.");

                // 1. File 객체로 Makesense 내부의 ImageData 구조 생성
                const imageData = ImageDataUtil.createImageDataFromFileData(file);

                // 2. 생성된 ImageData 객체를 배열에 담아 Redux 스토어에 디스패치
                // Makesense는 여러 이미지를 처리할 수 있으므로 배열에 담아 전달합니다.
                store.dispatch(addImageData([imageData]));

                console.log("ImageData created and dispatched to store.");

                // --- 추가된 부분: 프로젝트 타입 및 활성 이미지 인덱스 설정 ---
                // URL 로딩 시 기본 프로젝트 타입을 설정합니다. (예: 객체 탐지)
                // 필요에 따라 URL 파라미터로 프로젝트 타입을 받을 수도 있습니다.
                const projectType = ProjectType.OBJECT_DETECTION; // 기본값 설정
                store.dispatch(updateProjectData({
                    ...store.getState().general.projectData, // 기존 프로젝트 데이터 유지 (이름 등)
                    type: projectType
                }));
                console.log(`Project type set to: ${projectType}`);

                // 로드된 이미지가 하나뿐이므로 활성 이미지 인덱스를 0으로 설정합니다.
                store.dispatch(updateActiveImageIndex(0));
                console.log("Active image index set to 0.");
                // --------------------------------------------------------

                // TODO: 라벨 이름 설정 처리
                // ImagesDropZone에서는 파일 로딩 후 INSERT_LABEL_NAMES 팝업을 띄웁니다.
                // URL 로딩 시에도 라벨 이름 설정이 필요할 수 있습니다.
                // - 미리 정의된 라벨 이름 목록을 로드하거나
                // - 사용자에게 라벨 이름을 입력받는 팝업을 띄우거나 (ImagesDropZone 방식)
                // - Makesense의 기본 라벨 이름 설정을 사용하도록 처리해야 합니다.
                // 현재는 이 부분을 건너뛰므로, 라벨 이름이 설정되지 않아 문제가 될 수 있습니다.
                // store.dispatch(updateActivePopupType(PopupWindowType.INSERT_LABEL_NAMES)); // 필요하다면 이 액션을 디스패치

                // NOTE: Redux 스토어에 ImageData가 추가되고 상태가 업데이트되면, Makesense의 다른 부분(리듀서 또는 연결된 컴포넌트)에서
                // 이 상태 변화를 감지하고 ImageDataUtil.loadMissingImages 등을 호출하여 실제 이미지 픽셀 데이터를 로딩할 것으로 예상됩니다.
                // 이 부분은 Makesense의 기존 로직에 의존합니다.

            } else {
                console.error("Failed to create File object from URL.");
                // File 객체 생성 실패 시 오류 로그만 남깁니다.
            }
        } catch (error) {
            console.error("Error during image loading from URL process:", error);
            // 비동기 처리 중 예외 발생 시 오류 로그만 남깁니다.
        }
    } else {
        // URL 파라미터가 없으면 메시지만 출력
        console.log("No image_url parameter detected. Standard initialization.");
    }

    // 이미지 로딩 시도 완료 (성공/실패 여부와 관계없이) 후 초기화 루틴 실행
    // 프로젝트 타입 설정 등이 완료된 후에 초기화가 진행되도록 순서를 유지합니다.
    AppInitializer.inti();

    // ----------------------------------------------------------

    // React 애플리케이션 렌더링 시작
    const root = ReactDOM.createRoot(document.getElementById('root') || document.createElement('div'));
    root.render(
        <React.StrictMode>
            <Provider store={store}>
                <App />
            </Provider>
        </React.StrictMode>
    );

})(); // 즉시 실행 함수 종료
