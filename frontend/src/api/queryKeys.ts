// TanStack Query keys in one place (server state lives only in the query cache).
export const ME_KEY = ['me'] as const
export const CONFIG_KEY = ['config'] as const
export const WORLD_KEY = ['world'] as const
export const PROGRESS_KEY = ['progress'] as const
export const attemptKey = (attemptId: string) => ['attempt', attemptId] as const
export const reportKey = (attemptId: string) => ['report', attemptId] as const
export const TEACHER_CLASSES_KEY = ['teacher', 'classes'] as const
export const classProgressKey = (classId: string) => ['teacher', 'class', classId] as const
